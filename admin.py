from pyrogram import Client, filters, enums
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from database import set_setting, get_setting, get_db

user_states = {}

def setup_admin_handlers(app: Client, owner_id: int, send_start_panel_fn):
    
    # Clean & Professional Keyboard Layout
    admin_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("✏️ Set Promo Text"), KeyboardButton("❌ Remove Promo")],
            [KeyboardButton("🔑 Set Get Key"), KeyboardButton("❌ Remove Get Key")],
            [KeyboardButton("🔗 Set Click Here"), KeyboardButton("❌ Remove Click")],
            [KeyboardButton("🌐 Set Verify Link"), KeyboardButton("❌ Remove Verify")],
            [KeyboardButton("📢 Broadcast"), KeyboardButton("📊 Bot Stats")],
            [KeyboardButton("🖼️ Set Banner DP"), KeyboardButton("❌ Remove DP")],
            [KeyboardButton("🎙️ Set Voice Note"), KeyboardButton("❌ Remove Voice")],
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
        user_states.pop(message.from_user.id, None)
        await message.reply_text("⚙️ **Welcome to Admin Panel**\n\nNiche diye gaye buttons se bot ko control karein:", reply_markup=admin_keyboard)

    @app.on_message(filters.private & ~filters.command("start") & ~filters.command("admin"))
    async def handle_admin_inputs(client, message: Message):
        user_id = message.from_user.id
        if user_id != owner_id:
            return

        text = message.text

        menu_buttons = [
            "✏️ Set Promo Text", "❌ Remove Promo", 
            "🔑 Set Get Key", "❌ Remove Get Key", 
            "🔗 Set Click Here", "❌ Remove Click",
            "🌐 Set Verify Link", "❌ Remove Verify",
            "📢 Broadcast", "📊 Bot Stats",
            "🖼️ Set Banner DP", "❌ Remove DP", 
            "🎙️ Set Voice Note", "❌ Remove Voice", 
            "🟢 Check Status"
        ]

        if text in menu_buttons or (text and text.startswith("✅ SLOT ")):
            user_states.pop(user_id, None)

            if text == "✏️ Set Promo Text":
                user_states[user_id] = "SET_PROMO"
                return await message.reply_text("✏️ Send new Promo Text for /start:\n\nTip: Use {name} for user's full name.")
            
            elif text == "❌ Remove Promo":
                set_setting("promo_text", "")
                return await message.reply_text("✅ Promo Text Removed!")

            elif text == "🔑 Set Get Key":
                user_states[user_id] = "SET_GET_KEY"
                return await message.reply_text("🔑 Send new Get Key URL:")
                
            elif text == "❌ Remove Get Key":
                set_setting("get_key_url", "")
                return await message.reply_text("✅ Get Key Link Removed!")

            elif text == "🔗 Set Click Here":
                user_states[user_id] = "SET_CLICK_HERE"
                return await message.reply_text("🔗 Send Click Here URL:")
                
            elif text == "❌ Remove Click":
                set_setting("click_url", "")
                return await message.reply_text("✅ Click Here Link Removed!")

            elif text == "🌐 Set Verify Link":
                user_states[user_id] = "SET_VERIFY_URL"
                return await message.reply_text("🌐 Send Verify / Check Joined URL:")
                
            elif text == "❌ Remove Verify":
                set_setting("verify_url", "")
                return await message.reply_text("✅ Verify Link Removed!")

            elif text == "📢 Broadcast":
                user_states[user_id] = "BROADCAST"
                return await message.reply_text("📢 Send the message (Text, Photo, or Video) you want to broadcast to all users:")

            elif text == "📊 Bot Stats":
                total_users = get_db("SELECT COUNT(*) FROM users")
                count = total_users[0][0] if total_users else 0
                return await message.reply_text(f"📊 **Bot Statistics**\n\n👥 Total Users in Database: `{count}`")

            elif text == "🖼️ Set Banner DP":
                user_states[user_id] = "SET_DP"
                return await message.reply_text("🖼️ Send Banner Photo or Video:")
                
            elif text == "❌ Remove DP":
                set_setting("media_file_id", "")
                set_setting("media_type", "")
                return await message.reply_text("✅ DP Removed!")

            elif text == "🎙️ Set Voice Note":
                user_states[user_id] = "SET_VOICE"
                return await message.reply_text("🎙️ Send Voice Message for /start:")
                
            elif text == "❌ Remove Voice":
                set_setting("voice_file_id", "")
                return await message.reply_text("✅ Voice Removed!")
                
            elif text == "🟢 Check Status":
                return await message.reply_text("✅ Bot is Online and Working perfectly!")

            elif text.startswith("✅ SLOT "):
                slot_num = text.split(" ")[2]
                user_states[user_id] = f"SET_SLOT_{slot_num}"
                return await message.reply_text(f"✅ Send Data for SLOT {slot_num} in format:\nChannel ID | Channel Name | Invite Link\n\nTo remove send: `off`")

        # ---------------- STATE (DATA) HANDLERS ----------------
        state = user_states.get(user_id)
        if not state:
            return

        if state == "SET_PROMO":
            promo_html = message.text.html if message.text else (message.caption.html if message.caption else "")
            set_setting("promo_text", promo_html)
            user_states.pop(user_id, None)
            await message.reply_text("✅ Promo Text Updated Successfully!")

        elif state == "SET_GET_KEY":
            set_setting("get_key_url", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ Get Key Link Saved Successfully!")

        elif state == "SET_CLICK_HERE":
            set_setting("click_url", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ Click Here Link Saved Successfully!")

        elif state == "SET_VERIFY_URL":
            set_setting("verify_url", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ Verify Link Saved Successfully!")

        elif state == "BROADCAST":
            users = get_db("SELECT user_id FROM users")
            sent = 0
            failed = 0
            status_msg = await message.reply_text("📢 Broadcast in progress, please wait...")
            
            for u in users:
                u_id = u[0]
                try:
                    if message.photo:
                        await client.send_photo(u_id, photo=message.photo.file_id, caption=message.caption.html if message.caption else "", parse_mode=enums.ParseMode.HTML)
                    elif message.video:
                        await client.send_video(u_id, video=message.video.file_id, caption=message.caption.html if message.caption else "", parse_mode=enums.ParseMode.HTML)
                    else:
                        await client.send_message(u_id, text=message.text.html if message.text else "", parse_mode=enums.ParseMode.HTML)
                    sent += 1
                except Exception:
                    failed += 1
            
            user_states.pop(user_id, None)
            await status_msg.edit_text(f"✅ **Broadcast Completed!**\n\n📤 Successfully Sent: `{sent}`\n❌ Failed: `{failed}`")

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
