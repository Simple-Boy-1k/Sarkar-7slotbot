from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from database import set_setting, get_setting

user_states = {}

def setup_admin_handlers(app: Client, owner_id: int, send_start_panel_fn):
    
    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message: Message):
        if message.from_user.id != owner_id:
            return
        await send_admin_menu(message)

    async def send_admin_menu(message: Message):
        status = get_setting("bot_status") or "online"
        btn_status = "🔴 Set Bot Offline" if status == "online" else "🟢 Set Bot Online"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Set Promo Text", callback_data="admin_set_promo")],
            [InlineKeyboardButton("🔗 Set Click Here Button", callback_data="admin_set_click")],
            [InlineKeyboardButton("🔑 Set Get Key URL", callback_data="admin_set_key_url")],
            [InlineKeyboardButton(btn_status, callback_data="admin_toggle_status")],
            [InlineKeyboardButton("❌ Close", callback_data="admin_close")]
        ])
        await message.reply_text("⚙️ <b>Admin Control Panel</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

    @app.on_callback_query(filters.regex("^admin_"))
    async def admin_callbacks(client, callback: CallbackQuery):
        user_id = callback.from_user.id
        if user_id != owner_id:
            return await callback.answer("Unauthorized", show_alert=True)
        
        data = callback.data
        
        if data == "admin_set_promo":
            user_states[user_id] = "AWAITING_PROMO_TEXT"
            await callback.message.reply_text(
                "✏️ <b>Send new Promo Text for /start:</b>\n\n"
                "<i>Premium Emojis and Formatting supported!</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await callback.answer()

        elif data == "admin_set_click":
            user_states[user_id] = "AWAITING_CLICK_HERE"
            await callback.message.reply_text(
                "🔗 <b>Send Button Link:</b>\n\n"
                "• Aap <b>sirf link</b> bhej sakte hain (e.g. <code>https://t.me/...</code>)\n"
                "• Ya custom name ke saath: <code>Button Name | https://t.me/...</code>\n"
                "• Hataney ke liye <code>off</code> bhejein.",
                parse_mode=enums.ParseMode.HTML
            )
            await callback.answer()
        
        elif data == "admin_set_key_url":
            user_states[user_id] = "AWAITING_KEY_URL"
            await callback.message.reply_text(
                "🔑 <b>Send Get Key URL:</b>\n\n"
                "• Direct link bhejein (e.g. <code>https://t.me/...</code>)\n"
                "• Hataney ke liye <code>off</code> bhejein (How To Get Key section hide ho jayega).",
                parse_mode=enums.ParseMode.HTML
            )
            await callback.answer()
            
        elif data == "admin_toggle_status":
            curr = get_setting("bot_status") or "online"
            new_status = "offline" if curr == "online" else "online"
            set_setting("bot_status", new_status)
            await callback.answer(f"Bot Status: {new_status.upper()}", show_alert=True)
            await send_admin_menu(callback.message)
            
        elif data == "admin_close":
            await callback.message.delete()

    @app.on_message(filters.private & ~filters.command("start") & ~filters.command("admin"))
    async def handle_admin_inputs(client, message: Message):
        user_id = message.from_user.id
        if user_id != owner_id or user_id not in user_states:
            return
        
        state = user_states.pop(user_id, None)
        
        if state == "AWAITING_PROMO_TEXT":
            # Preservation of Premium Emoji HTML tags
            promo_html = message.text.html if message.text else (message.caption.html if message.caption else "")
            set_setting("promo_text", promo_html)
            await message.reply_text("✅ <b>Promo Text Updated with Premium Emojis!</b>", parse_mode=enums.ParseMode.HTML)

        elif state == "AWAITING_CLICK_HERE":
            text = message.text.strip() if message.text else ""
            if text.lower() in ["off", "remove", "clear"]:
                set_setting("click_name", "")
                set_setting("click_url", "")
                return await message.reply_text("✅ <b>Click Here button removed!</b>", parse_mode=enums.ParseMode.HTML)

            if "|" in text:
                parts = text.split("|", 1)
                btn_name = parts[0].strip()
                btn_url = parts[1].strip()
            else:
                btn_name = "Click Here"
                btn_url = text
            
            set_setting("click_name", btn_name)
            set_setting("click_url", btn_url)
            await message.reply_text(
                f"✅ <b>Click Here Button Saved!</b>\n\n"
                f"<b>Button Text:</b> {btn_name}\n"
                f"<b>URL:</b> {btn_url}", 
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
            
        elif state == "AWAITING_KEY_URL":
            text = message.text.strip() if message.text else ""
            if text.lower() in ["off", "remove", "clear"]:
                set_setting("get_key_url", "")
                return await message.reply_text("✅ <b>Get Key URL removed! 'How To Get Key' section is now hidden.</b>", parse_mode=enums.ParseMode.HTML)

            set_setting("get_key_url", text)
            await message.reply_text(
                f"✅ <b>Get Key URL Updated!</b>\n\n"
                f"<b>Link:</b> {text}\n\n"
                f"<i>Ab /start message me 'How To Get Key' dikhega.</i>", 
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True
            )
