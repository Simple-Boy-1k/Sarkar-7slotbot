from pyrogram import Client, filters, enums
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from database import set_setting, get_setting, get_db

user_states = {}

def setup_admin_handlers(app: Client, owner_id: int, send_start_panel_fn):
    
    # Aapka Custom Admin Menu (Niche aane wale bade buttons)
    admin_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("✏️ Set Text Promo"), KeyboardButton("❌ Remove Promo Text")],
            [KeyboardButton("🔑 Set GET KEY Link"), KeyboardButton("❌ Remove GET KEY Link")],
            [KeyboardButton("🖼️ Set DP"), KeyboardButton("❌ Remove DP")],
            [KeyboardButton("🔗 Set Click Here"), KeyboardButton("❌ Remove Click Here Link")],
            [KeyboardButton("🎙️ Set Voice"), KeyboardButton("❌ Remove Voice")],
            [KeyboardButton("✅ SLOT 1"), KeyboardButton("✅ SLOT 2")],
            [KeyboardButton("✅ SLOT 3"), KeyboardButton("✅ SLOT 4")],
            [KeyboardButton("✅ SLOT 5"), KeyboardButton("✅ SLOT 6")],
            [KeyboardButton("✅ SLOT 7"), KeyboardButton("🟢 Check Status")]
        ],
        resize_keyboard=True
    )

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message: Message):
        if message.from_user.id != owner_id:
            return
        await message.reply_text("⚙️ **Welcome to Admin Panel**\n\nNiche diye gaye buttons se bot control karein:", reply_markup=admin_keyboard)

    @app.on_message(filters.private & ~filters.command("start") & ~filters.command("admin"))
    async def handle_admin_inputs(client, message: Message):
        user_id = message.from_user.id
        if user_id != owner_id:
            return

        text = message.text

        # ---------------- BUTTON CLICKS HANDLERS ----------------
        if text == "✏️ Set Text Promo":
            user_states[user_id] = "SET_PROMO"
            return await message.reply_text("✏️ Send new Promo Text for /start:\n\nTip: Use {name} for user's full name.")
        
        elif text == "❌ Remove Promo Text":
            set_setting("promo_text", "")
            return await message.reply_text("✅ Promo Text Removed!")

        elif text == "🔑 Set GET KEY Link":
            user_states[user_id] = "SET_GET_KEY"
            return await message.reply_text("🔑 Send new GET KEY URL:")
            
        elif text == "❌ Remove GET KEY Link":
            set_setting("get_key_url", "")
            return await message.reply_text("✅ GET KEY Link Removed! 'How To Get Key' section is hidden.")

        elif text == "🖼️ Set DP":
            user_states[user_id] = "SET_DP"
            return await message.reply_text("🖼️ Send Banner Photo or Video:")
            
        elif text == "❌ Remove DP":
            set_setting("media_file_id", "")
            set_setting("media_type", "")
            return await message.reply_text("✅ DP Removed!")

        elif text == "🔗 Set Click Here":
            user_states[user_id] = "SET_CLICK_HERE"
            return await message.reply_text("🔗 Send format: Button Name | https://link.com\n\n(Aap chahein toh sirf link bhi bhej sakte hain!)")
            
        elif text == "❌ Remove Click Here Link":
            set_setting("click_name", "")
            set_setting("click_url", "")
            return await message.reply_text("✅ Click Here Link Removed!")

        elif text == "🎙️ Set Voice":
            user_states[user_id] = "SET_VOICE"
            return await message.reply_text("🎙️ Send Voice Message for /start:")
            
        elif text == "❌ Remove Voice":
            set_setting("voice_file_id", "")
            return await message.reply_text("✅ Voice Removed!")
            
        elif text == "🟢 Check Status":
            return await message.reply_text("✅ Bot is Online and Working perfectly!")

        # SLOT HANDLERS
        elif text and text.startswith("✅ SLOT "):
            slot_num = text.split(" ")[2]
            user_states[user_id] = f"SET_SLOT_{slot_num}"
            return await message.reply_text(f"✅ Send Data for SLOT {slot_num} in format:\nChannel ID | Channel Name | Invite Link\n\nTo remove send: `off`")

        # ---------------- STATE (DATA) HANDLERS ----------------
        state = user_states.get(user_id)
        if not state:
            return

        # 1. Premium Emoji Promo Text Save
        if state == "SET_PROMO":
            promo_html = message.text.html if message.text else (message.caption.html if message.caption else "")
            set_setting("promo_text", promo_html)
            user_states.pop(user_id, None)
            await message.reply_text("✅ Promo Text Updated Successfully!")

        elif state == "SET_GET_KEY":
            set_setting("get_key_url", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ GET KEY Link Updated!")

        elif state == "SET_DP":
            if message.photo:
                set_setting("media_file_id", message.photo.file_id)
                set_setting("media_type", "photo")
                user_states.pop(user_id, None)
                await message.reply_text("✅ DP Updated (Photo)!")
            elif message.video:
                set_setting("media_file_id", message.video.file_id)
                set_setting("media_type", "video")
                user_states.pop(user_id, None)
                await message.reply_text("✅ DP Updated (Video)!")
            else:
                await message.reply_text("❌ Please send a valid Photo or Video.")

        elif state == "SET_VOICE":
            if message.voice:
                set_setting("voice_file_id", message.voice.file_id)
                user_states.pop(user_id, None)
                await message.reply_text("✅ Voice Updated!")
            else:
                await message.reply_text("❌ Please send a valid Voice message.")

        # 2. Click Here Button Save (Bina '|' wale error ke)
        elif state == "SET_CLICK_HERE":
            input_text = message.text.strip() if message.text else ""
            
            if "|" in input_text:
                parts = input_text.split("|", 1)
                btn_name = parts[0].strip()
                btn_url = parts[1].strip()
            else:
                # Agar usne format use nahi kiya, sirf link daala toh:
                btn_name = "Click Here"
                btn_url = input_text

            set_setting("click_name", btn_name)
            set_setting("click_url", btn_url)
            user_states.pop(user_id, None)
            await message.reply_text(f"✅ Click Here Button Saved!\n\nName: {btn_name}\nURL: {btn_url}", disable_web_page_preview=True)

        # 3. Slots Manager
        elif state.startswith("SET_SLOT_"):
            slot_id = state.split("_")[2]
            input_text = message.text.strip() if message.text else ""
            
            if input_text.lower() == "off":
                get_db("UPDATE slots SET chat_id = '', name = '', link = '' WHERE id = ?", (int(slot_id),), commit=True)
                user_states.pop(user_id, None)
                return await message.reply_text(f"✅ SLOT {slot_id} Removed!")

            if "|" not in input_text:
                return await message.reply_text("❌ Format galat hai! Aise bhejein: Channel ID | Channel Name | Invite Link")
            
            parts = input_text.split("|")
            if len(parts) != 3:
                return await message.reply_text("❌ Format galat hai! Aise bhejein: Channel ID | Channel Name | Invite Link")
            
            chat_id, name, link = [p.strip() for p in parts]
            get_db("UPDATE slots SET chat_id = ?, name = ?, link = ? WHERE id = ?", (chat_id, name, link, int(slot_id)), commit=True)
            user_states.pop(user_id, None)
            await message.reply_text(f"✅ SLOT {slot_id} Updated Successfully!")
