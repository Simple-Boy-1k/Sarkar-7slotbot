from pyrogram import Client, filters, enums
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from database import set_setting, get_setting, get_db

user_states = {}

def setup_admin_handlers(app: Client, owner_id: int, send_start_panel_fn):
    
    admin_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("✏️ Set Promo Text"), KeyboardButton("❌ Remove Promo")],
            [KeyboardButton("🔑 Set Get Key"), KeyboardButton("❌ Remove Get Key")],
            [KeyboardButton("🔗 Set Click Here"), KeyboardButton("❌ Remove Click")],
            [KeyboardButton("🌐 Set Verify Link"), KeyboardButton("❌ Remove Verify")],
            [KeyboardButton("✅ ꜱʟᴏᴛ 1"), KeyboardButton("✅ ꜱʟᴏᴛ 2")],
            [KeyboardButton("✅ ꜱʟᴏᴛ 3"), KeyboardButton("✅ ꜱʟᴏᴛ 4")],
            [KeyboardButton("✅ ꜱʟᴏᴛ 5"), KeyboardButton("✅ ꜱʟᴏᴛ 6")],
            [KeyboardButton("✅ ꜱʟᴏᴛ 7")],
            [KeyboardButton("❌ Remove ꜱʟᴏᴛ 1"), KeyboardButton("❌ Remove ꜱʟᴏᴛ 2")],
            [KeyboardButton("❌ Remove ꜱʟᴏᴛ 3"), KeyboardButton("❌ Remove ꜱʟᴏᴛ 4")],
            [KeyboardButton("❌ Remove ꜱʟᴏᴛ 5"), KeyboardButton("❌ Remove ꜱʟᴏᴛ 6")],
            [KeyboardButton("❌ Remove ꜱʟᴏᴛ 7")],
            [KeyboardButton("📢 Broadcast"), KeyboardButton("📊 Stats User")],
            [KeyboardButton("🖼️ Set Banner DP"), KeyboardButton("❌ Remove DP")],
            [KeyboardButton("🎙️ Set Voice Note"), KeyboardButton("❌ Remove Voice")],
            [KeyboardButton("❌ Bot Offline"), KeyboardButton("✅ Bot Online")],
            [KeyboardButton("📴 Set Offline Channel"), KeyboardButton("❌ Remove Offline Channel")],
            [KeyboardButton("🧹 Clear Cache"), KeyboardButton("🚀 Start Bot")]
        ],
        resize_keyboard=True
    )

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message: Message):
        if message.from_user.id != owner_id:
            return
        user_states.pop(message.from_user.id, None)
        await message.reply_text("👑 **ADMIN PANEL**\n\nNiche diye gaye buttons se bot control karein:", reply_markup=admin_keyboard)

    @app.on_message(filters.private & ~filters.command("start") & ~filters.command("admin"))
    async def handle_admin_inputs(client, message: Message):
        user_id = message.from_user.id
        if user_id != owner_id:
            return

        text = message.text.strip() if message.text else ""
        lower_text = text.lower()

        # 100% Working Flexible Slot & Remove Slot Handlers
        slot_matched = False
        for n in range(1, 8):
            if str(n) in text and ("ꜱʟᴏﺕ" in text or "slot" in text or "ꜱʟ𝗼𝘁" in text):
                if "remove" in lower_text:
                    get_db("UPDATE slots SET chat_id = '', name = '', link = '' WHERE id = ?", (n,), commit=True)
                    slot_matched = True
                    return await message.reply_text(f"❌ SLOT {n} Removed Successfully!")
                else:
                    user_states[user_id] = f"SET_SLOT_{n}"
                    slot_matched = True
                    return await message.reply_text(f"✅ Send link for **SLOT {n}** (Seedha link bhej sakte hain, save ho jayega):")
        
        if slot_matched:
            return

        if "set promo text" in lower_text or "promo text" in lower_text:
            user_states[user_id] = "SET_PROMO"
            return await message.reply_text("✏️ Send new Promo Text for /start:")
        
        elif "remove promo" in lower_text:
            set_setting("promo_text", "")
            return await message.reply_text("✅ Promo Text Removed!")

        elif "set get key" in lower_text:
            user_states[user_id] = "SET_GET_KEY"
            return await message.reply_text("🔑 Send new Get Key URL:")
            
        elif "remove get key" in lower_text:
            set_setting("get_key_url", "")
            return await message.reply_text("✅ Get Key Link Removed!")

        elif "set click here" in lower_text:
            user_states[user_id] = "SET_CLICK_HERE"
            return await message.reply_text("🔗 Send Click Here URL:")
            
        elif "remove click" in lower_text:
            set_setting("click_url", "")
            return await message.reply_text("✅ Click Here Link Removed!")

        elif "set verify" in lower_text or "verify link" in lower_text:
            user_states[user_id] = "SET_VERIFY"
            return await message.reply_text("🌐 Send Verify / Check Joined URL:")
            
        elif "remove verify" in lower_text:
            set_setting("verify_url", "")
            return await message.reply_text("✅ Verify Link Removed!")

        elif "broadcast" in lower_text:
            user_states[user_id] = "BROADCAST"
            return await message.reply_text("📢 Send the message (Text, Photo, or Video) to broadcast:")

        elif "stats user" in lower_text:
            total_users = get_db("SELECT COUNT(*) FROM users")
            count = total_users[0][0] if total_users else 0
            return await message.reply_text(f"📊 **Total Users in Database:** `{count}`")

        elif "bot offline" in lower_text:
            set_setting("bot_status", "offline")
            return await message.reply_text("❌ Bot is now set to **OFFLINE** mode.")

        elif "bot online" in lower_text:
            set_setting("bot_status", "online")
            return await message.reply_text("✅ Bot is now set to **ONLINE** mode.")

        elif "set offline channel" in lower_text:
            user_states[user_id] = "SET_OFFLINE_CHAN"
            return await message.reply_text("📴 Send Offline Maintenance Channel Link:")

        elif "remove offline channel" in lower_text:
            set_setting("offline_channel", "")
            return await message.reply_text("✅ Offline Channel Removed!")

        elif "clear cache" in lower_text:
            user_states.clear()
            return await message.reply_text("🧹 Cache cleared successfully!")

        elif "start bot" in lower_text:
            return await send_start_panel_fn(client, message, user_id)

        elif "set banner dp" in lower_text or ("dp" in lower_text and "set" in lower_text):
            user_states[user_id] = "SET_DP"
            return await message.reply_text("🖼️ Send Banner Photo or Video:")
            
        elif "remove dp" in lower_text:
            set_setting("media_file_id", "")
            set_setting("media_type", "")
            return await message.reply_text("✅ DP Removed!")

        elif "set voice note" in lower_text or ("voice" in lower_text and "set" in lower_text):
            user_states[user_id] = "SET_VOICE"
            return await message.reply_text("🎙️ Send Voice Message:")
            
        elif "remove voice" in lower_text:
            set_setting("voice_file_id", "")
            return await message.reply_text("✅ Voice Removed!")

        # ---------------- STATE HANDLERS ----------------
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

        elif state == "SET_VERIFY":
            set_setting("verify_url", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ Verify Link Saved Successfully!")

        elif state == "SET_OFFLINE_CHAN":
            set_setting("offline_channel", message.text.strip())
            user_states.pop(user_id, None)
            await message.reply_text("✅ Offline Channel Saved Successfully!")

        elif state == "BROADCAST":
            users = get_db("SELECT user_id FROM users")
            sent = 0
            failed = 0
            status_msg = await message.reply_text("📢 Broadcast in progress...")
            
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
            await status_msg.edit_text(f"✅ **Broadcast Completed!**\n\n📤 Sent: `{sent}`\n❌ Failed: `{failed}`")

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

            if "|" in input_text:
                parts = input_text.split("|")
                chat_id = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else f"Channel {slot_id}"
                link = parts[2].strip() if len(parts) > 2 else parts[-1].strip()
            else:
                link = input_text
                chat_id = input_text
                name = f"Channel {slot_id}"
            
            get_db("UPDATE slots SET chat_id = ?, name = ?, link = ? WHERE id = ?", (chat_id, name, link, int(slot_id)), commit=True)
            user_states.pop(user_id, None)
            await message.reply_text(f"✅ SLOT {slot_id} Saved Successfully!\n\n🔗 Link: {link}")
