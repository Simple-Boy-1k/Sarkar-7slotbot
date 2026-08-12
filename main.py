from pyrogram import filters, enums
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from database import get_db, get_setting, set_setting, is_owner, is_admin

user_states = {}

def get_owner_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ Add Admin"), KeyboardButton("❌ Remove Admin")],
            [KeyboardButton("📋 Admin List")],
            [KeyboardButton("👥 Stats User")],
            [KeyboardButton("🗑️ Clear Stats User")],
            [KeyboardButton("❌ Bot Offline"), KeyboardButton("✅ Bot Online")],
            [KeyboardButton("🚀 Start Bot")],
            [KeyboardButton("✏️ Set Text Promo"), KeyboardButton("❌ Remove Promo Text")],
            [KeyboardButton("🔑 Set GET KEY Link"), KeyboardButton("❌ Remove GET KEY Link")],
            [KeyboardButton("🖼️ Set DP"), KeyboardButton("❌ Remove DP")],
            [KeyboardButton("🔗 Set Click Here"), KeyboardButton("❌ Remove Click Here Link")],
            [KeyboardButton("🎙️ Set Voice"), KeyboardButton("❌ Remove Voice")],
            [KeyboardButton("✅ SLOT 1"), KeyboardButton("✅ SLOT 2")],
            [KeyboardButton("✅ SLOT 3"), KeyboardButton("✅ SLOT 4")],
            [KeyboardButton("✅ SLOT 5"), KeyboardButton("✅ SLOT 6")],
            [KeyboardButton("✅ SLOT 7")],
            [KeyboardButton("❌ Remove SLOT 1"), KeyboardButton("❌ Remove SLOT 2")],
            [KeyboardButton("❌ Remove SLOT 3"), KeyboardButton("❌ Remove SLOT 4")],
            [KeyboardButton("❌ Remove SLOT 5"), KeyboardButton("❌ Remove SLOT 6")],
            [KeyboardButton("❌ Remove SLOT 7")],
            [KeyboardButton("✅ Verify"), KeyboardButton("❌ Remove Verify")],
            [KeyboardButton("📢 Broadcast"), KeyboardButton("📊 Broadcast Status")],
            [KeyboardButton("⛔ Stop Broadcast")],
            [KeyboardButton("📴 Set Offline Channel"), KeyboardButton("❌ Remove Offline Channel")],
            [KeyboardButton("🧹 Clear Cache")],
            [KeyboardButton("👑 OWNER PANEL")]
        ],
        resize_keyboard=True
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("👥 Stats User")],
            [KeyboardButton("❌ Bot Offline"), KeyboardButton("✅ Bot Online")],
            [KeyboardButton("🚀 Start Bot")],
            [KeyboardButton("✏️ Set Text Promo"), KeyboardButton("❌ Remove Promo Text")],
            [KeyboardButton("🔑 Set GET KEY Link"), KeyboardButton("❌ Remove GET KEY Link")],
            [KeyboardButton("🖼️ Set DP"), KeyboardButton("❌ Remove DP")],
            [KeyboardButton("🔗 Set Click Here"), KeyboardButton("❌ Remove Click Here Link")],
            [KeyboardButton("🎙️ Set Voice"), KeyboardButton("❌ Remove Voice")],
            [KeyboardButton("✅ SLOT 1"), KeyboardButton("✅ SLOT 2")],
            [KeyboardButton("✅ SLOT 3"), KeyboardButton("✅ SLOT 4")],
            [KeyboardButton("✅ SLOT 5"), KeyboardButton("✅ SLOT 6")],
            [KeyboardButton("✅ SLOT 7")],
            [KeyboardButton("❌ Remove SLOT 1"), KeyboardButton("❌ Remove SLOT 2")],
            [KeyboardButton("❌ Remove SLOT 3"), KeyboardButton("❌ Remove SLOT 4")],
            [KeyboardButton("❌ Remove SLOT 5"), KeyboardButton("❌ Remove SLOT 6")],
            [KeyboardButton("❌ Remove SLOT 7")],
            [KeyboardButton("✅ Verify"), KeyboardButton("❌ Remove Verify")],
            [KeyboardButton("📴 Set Offline Channel"), KeyboardButton("❌ Remove Offline Channel")],
            [KeyboardButton("🧹 Clear Cache")],
            [KeyboardButton("🛡️ ADMIN PANEL")]
        ],
        resize_keyboard=True
    )

def setup_admin_handlers(app, OWNER_ID, start_panel_func):

    @app.on_message(filters.command("admin"))
    async def admin_cmd(client, message: Message):
        user_id = message.from_user.id
        if is_owner(user_id, OWNER_ID):
            await message.reply_text("👑 <b>OWNER CONTROL PANEL ACTIVE</b>", reply_markup=get_owner_keyboard(), parse_mode=enums.ParseMode.HTML)
        elif is_admin(user_id, OWNER_ID):
            await message.reply_text("🛡️ <b>ADMIN CONTROL PANEL ACTIVE</b>", reply_markup=get_admin_keyboard(), parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text("❌ Access Denied")

    @app.on_message(filters.private & ~filters.command(["start", "admin"]))
    async def handle_admin_buttons(client, message: Message):
        user_id = message.from_user.id
        text = message.text or ""
        state = user_states.get(user_id)

        if not is_admin(user_id, OWNER_ID):
            return

        # OWNER-ONLY BUTTONS
        if is_owner(user_id, OWNER_ID):
            if text == "➕ Add Admin":
                user_states[user_id] = "ADD_ADMIN"
                return await message.reply_text("👤 Send Telegram User ID of new Admin:")
            elif text == "❌ Remove Admin":
                user_states[user_id] = "DEL_ADMIN"
                return await message.reply_text("🗑️ Send Telegram User ID to remove Admin:")
            elif text == "📋 Admin List":
                admins = get_db("SELECT user_id FROM admins")
                ad_list = "\n".join([f"• <code>{a[0]}</code>" for a in admins]) or "No admins added."
                return await message.reply_text(f"📋 <b>ADMIN LIST:</b>\n\nOwner: <code>{OWNER_ID}</code>\n\n{ad_list}", parse_mode=enums.ParseMode.HTML)
            elif text == "🗑️ Clear Stats User":
                get_db("DELETE FROM users", commit=True)
                return await message.reply_text("✅ All user stats cleared!")
            elif text == "📢 Broadcast":
                user_states[user_id] = "BROADCAST"
                return await message.reply_text("📢 Send broadcast message:")
            elif text == "📊 Broadcast Status":
                return await message.reply_text("📊 Broadcast System Ready.")
            elif text == "⛔ Stop Broadcast":
                return await message.reply_text("⛔ Broadcast Stopped.")

        # SHARED CONTROL BUTTONS
        if text in ["👑 OWNER PANEL", "🛡️ ADMIN PANEL"]:
            kb = get_owner_keyboard() if is_owner(user_id, OWNER_ID) else get_admin_keyboard()
            return await message.reply_text("✅ Panel refreshed.", reply_markup=kb)

        elif text == "👥 Stats User":
            count = get_db("SELECT COUNT(*) FROM users", one=True)[0]
            return await message.reply_text(f"👥 <b>Total Users:</b> <code>{count}</code>", parse_mode=enums.ParseMode.HTML)

        elif text == "❌ Bot Offline":
            set_setting("bot_status", "offline")
            return await message.reply_text("❌ Bot is now <b>Offline</b>.", parse_mode=enums.ParseMode.HTML)

        elif text == "✅ Bot Online":
            set_setting("bot_status", "online")
            return await message.reply_text("✅ Bot is now <b>Online</b>.", parse_mode=enums.ParseMode.HTML)

        elif text == "🚀 Start Bot":
            await start_panel_func(client, message, user_id)

        elif text == "✏️ Set Text Promo":
            user_states[user_id] = "SET_PROMO"
            return await message.reply_text("✏️ Send new Promo Text for <code>/start</code>:", parse_mode=enums.ParseMode.HTML)

        elif text == "❌ Remove Promo Text":
            set_setting("promo_text", None)
            return await message.reply_text("✅ Promo text reset to default.")

        elif text == "🔑 Set GET KEY Link":
            user_states[user_id] = "SET_GET_KEY"
            return await message.reply_text("🔑 Send your GET KEY URL:")

        elif text == "❌ Remove GET KEY Link":
            set_setting("get_key_url", None)
            return await message.reply_text("✅ GET KEY link removed.")

        elif text == "🖼️ Set DP":
            user_states[user_id] = "SET_DP"
            return await message.reply_text("🖼️ Send Banner Photo or Video:")

        elif text == "❌ Remove DP":
            set_setting("media_type", None)
            set_setting("media_file_id", None)
            return await message.reply_text("✅ Banner DP/Video removed.")

        elif text == "🔗 Set Click Here":
            user_states[user_id] = "SET_CLICK"
            return await message.reply_text("🔗 Send format: <code>Button Name | https://link.com</code>", parse_mode=enums.ParseMode.HTML)

        elif text == "❌ Remove Click Here Link":
            set_setting("click_name", None)
            set_setting("click_url", None)
            return await message.reply_text("✅ Custom Click Link removed.")

        elif text == "🎙️ Set Voice":
            user_states[user_id] = "SET_VOICE"
            return await message.reply_text("🎙️ Record & send a Voice Note:")

        elif text == "❌ Remove Voice":
            set_setting("voice_file_id", None)
            return await message.reply_text("✅ Voice Note removed.")

        elif text.startswith("✅ SLOT "):
            slot_num = text.replace("✅ SLOT ", "").strip()
            user_states[user_id] = f"SET_SLOT_{slot_num}"
            return await message.reply_text(f"⚙️ Send Slot {slot_num} Link or Details:\n• Direct Link: <code>https://t.me/...</code>\n• Full Format: <code>ChatID | Name | Link</code>", parse_mode=enums.ParseMode.HTML)

        elif text.startswith("❌ Remove SLOT "):
            slot_num = text.replace("❌ Remove SLOT ", "").strip()
            get_db("UPDATE slots SET chat_id='', name='', link='' WHERE id=?", (slot_num,), commit=True)
            return await message.reply_text(f"✅ SLOT {slot_num} Removed!")

        elif text == "📴 Set Offline Channel":
            user_states[user_id] = "SET_OFFLINE_CHAN"
            return await message.reply_text("📴 Send Offline Channel link:")

        elif text == "❌ Remove Offline Channel":
            set_setting("offline_channel", None)
            return await message.reply_text("✅ Offline channel link reset.")

        elif text == "🧹 Clear Cache":
            return await message.reply_text("🧹 Cache cleared successfully!")

        # STATE PROCESSING LOGIC
        if state == "ADD_ADMIN" and is_owner(user_id, OWNER_ID):
            try:
                aid = int(text.strip())
                get_db("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (aid,), commit=True)
                user_states.pop(user_id, None)
                return await message.reply_text(f"✅ Admin <code>{aid}</code> Added!", parse_mode=enums.ParseMode.HTML)
            except Exception:
                return await message.reply_text("❌ Send numeric User ID!")

        elif state == "DEL_ADMIN" and is_owner(user_id, OWNER_ID):
            try:
                aid = int(text.strip())
                get_db("DELETE FROM admins WHERE user_id=?", (aid,), commit=True)
                user_states.pop(user_id, None)
                return await message.reply_text(f"✅ Admin <code>{aid}</code> Removed!", parse_mode=enums.ParseMode.HTML)
            except Exception:
                return await message.reply_text("❌ Send numeric User ID!")

        elif state == "SET_DP":
            if message.photo:
                set_setting("media_type", "photo")
                set_setting("media_file_id", message.photo.file_id)
                user_states.pop(user_id, None)
                return await message.reply_text("✅ Photo DP Banner Updated!")
            elif message.video:
                set_setting("media_type", "video")
                set_setting("media_file_id", message.video.file_id)
                user_states.pop(user_id, None)
                return await message.reply_text("✅ Video Banner Updated!")

        elif state == "SET_VOICE":
            if message.voice:
                set_setting("voice_file_id", message.voice.file_id)
                user_states.pop(user_id, None)
                return await message.reply_text("✅ Voice Note Updated!")

        elif state == "SET_PROMO":
            set_setting("promo_text", text)
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Promo Text Updated!")

        elif state == "SET_GET_KEY":
            set_setting("get_key_url", text.strip())
            user_states.pop(user_id, None)
            return await message.reply_text("✅ GET KEY Link Saved!")

        elif state == "SET_CLICK":
            try:
                p = [x.strip() for x in text.split("|")]
                set_setting("click_name", p[0])
                set_setting("click_url", p[1])
                user_states.pop(user_id, None)
                return await message.reply_text("✅ Custom Link Updated!")
            except Exception:
                return await message.reply_text("❌ Format: <code>Name | https://link.com</code>", parse_mode=enums.ParseMode.HTML)

        elif state == "SET_OFFLINE_CHAN":
            set_setting("offline_channel", text.strip())
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Offline Channel Link Saved!")

        elif state and state.startswith("SET_SLOT_"):
            slot_id = int(state.replace("SET_SLOT_", ""))
            parts = [x.strip() for x in text.split("|")]
            
            chat_id = ""
            name = f"Channel {slot_id}"
            link = ""

            if len(parts) == 3:
                chat_id, name, link = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                if parts[0].startswith("-100") or parts[0].isdigit():
                    chat_id, link = parts[0], parts[1]
                else:
                    name, link = parts[0], parts[1]
            elif len(parts) == 1:
                link = parts[0]
                if "t.me/" in link and not "+" in link and not "joinchat" in link:
                    clean_name = link.split("t.me/")[-1].replace("@", "").split("/")[0]
                    if clean_name:
                        chat_id = f"@{clean_name}"

            if "t.me" in link or "telegram.me" in link:
                get_db("UPDATE slots SET chat_id=?, name=?, link=? WHERE id=?", (chat_id, name, link, slot_id), commit=True)
                user_states.pop(user_id, None)
                return await message.reply_text(
                    f"✅ <b>SLOT {slot_id} Saved Successfully!</b>\n\n"
                    f"📌 <b>Name:</b> <code>{name}</code>\n"
                    f"🆔 <b>ChatID:</b> <code>{chat_id or 'Auto/Direct Link'}</code>\n"
                    f"🔗 <b>Link:</b> {link}",
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                return await message.reply_text("❌ Kripya valid Telegram link (<code>https://t.me/...</code>) bhejein!", parse_mode=enums.ParseMode.HTML)

        elif state == "BROADCAST" and is_owner(user_id, OWNER_ID):
            users = get_db("SELECT user_id FROM users")
            s, f = 0, 0
            for u in users:
                try:
                    await message.copy(u[0])
                    s += 1
                except Exception:
                    f += 1
            user_states.pop(user_id, None)
            return await message.reply_text(f"📢 <b>Broadcast Finished!</b>\n\n✅ Sent: <code>{s}</code>\n❌ Failed: <code>{f}</code>", parse_mode=enums.ParseMode.HTML)
