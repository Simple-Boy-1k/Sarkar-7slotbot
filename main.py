import os
import sqlite3
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, Message
)

# ----------------- CONFIGURATION ----------------- #
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

app = Client("Sarkar_7Slot_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ----------------- DATABASE SETUP ----------------- #
def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS slots (id INTEGER PRIMARY KEY, chat_id TEXT, name TEXT, link TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    
    for i in range(1, 8):
        cur.execute("INSERT OR IGNORE INTO slots (id, chat_id, name, link) VALUES (?, '', '', '')", (i,))
    
    conn.commit()
    conn.close()

init_db()

def get_db(sql, params=(), one=False, commit=False):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute(sql, params)
    if commit:
        conn.commit()
        res = True
    else:
        res = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return res

def get_setting(key, default=None):
    res = get_db("SELECT val FROM settings WHERE key=?", (key,), one=True)
    return res[0] if res else default

def set_setting(key, val):
    if val is None:
        get_db("DELETE FROM settings WHERE key=?", (key,), commit=True)
    else:
        get_db("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (key, str(val)), commit=True)

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    if is_owner(user_id):
        return True
    res = get_db("SELECT user_id FROM admins WHERE user_id=?", (user_id,), one=True)
    return bool(res)

# ----------------- KEYBOARDS SETUP ----------------- #

OWNER_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("➕ Add Admin"), KeyboardButton("❌ Remove Admin")],
        [KeyboardButton("📋 Admin List")],
        [KeyboardButton("👥 Stats User")],
        [KeyboardButton("🗑️ Clear Stats User")],
        [KeyboardButton("❌ Bot Offline"), KeyboardButton("✅ Bot Online")],
        [KeyboardButton("🚀 Start Bot")],
        [KeyboardButton("✏️ Set Text Promo")],
        [KeyboardButton("❌ Remove Promo Text")],
        [KeyboardButton("🖼️ Set DP"), KeyboardButton("❌ Remove DP")],
        [KeyboardButton("🔗 Set Click Here")],
        [KeyboardButton("❌ Remove Click Here Link")],
        [KeyboardButton("🎙️ Set Voice"), KeyboardButton("❌ Remove Voice")],
        [KeyboardButton("✅ SLOT 1"), KeyboardButton("✅ SLOT 2")],
        [KeyboardButton("✅ SLOT 3"), KeyboardButton("✅ SLOT 4")],
        [KeyboardButton("✅ SLOT 5"), KeyboardButton("✅ SLOT 6")],
        [KeyboardButton("✅ SLOT 7")],
        [KeyboardButton("❌ Remove SLOT 1"), KeyboardButton("❌ Remove SLOT 2")],
        [KeyboardButton("❌ Remove SLOT 3"), KeyboardButton("❌ Remove SLOT 4")],
        [KeyboardButton("❌ Remove SLOT 5"), KeyboardButton("❌ Remove SLOT 6")],
        [KeyboardButton("❌ Remove SLOT 7")],
        [KeyboardButton("✅ Verify")],
        [KeyboardButton("❌ Remove Verify")],
        [KeyboardButton("📢 Broadcast")],
        [KeyboardButton("📊 Broadcast Status")],
        [KeyboardButton("⛔ Stop Broadcast")],
        [KeyboardButton("📴 Set Offline Channel")],
        [KeyboardButton("❌ Remove Offline Channel")],
        [KeyboardButton("🧹 Clear Cache")],
        [KeyboardButton("👑 OWNER PANEL")]
    ],
    resize_keyboard=True
)

ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("👥 Stats User")],
        [KeyboardButton("❌ Bot Offline"), KeyboardButton("✅ Bot Online")],
        [KeyboardButton("🚀 Start Bot")],
        [KeyboardButton("✏️ Set Text Promo")],
        [KeyboardButton("❌ Remove Promo Text")],
        [KeyboardButton("🖼️ Set DP"), KeyboardButton("❌ Remove DP")],
        [KeyboardButton("🔗 Set Click Here")],
        [KeyboardButton("❌ Remove Click Here Link")],
        [KeyboardButton("🎙️ Set Voice"), KeyboardButton("❌ Remove Voice")],
        [KeyboardButton("✅ SLOT 1"), KeyboardButton("✅ SLOT 2")],
        [KeyboardButton("✅ SLOT 3"), KeyboardButton("✅ SLOT 4")],
        [KeyboardButton("✅ SLOT 5"), KeyboardButton("✅ SLOT 6")],
        [KeyboardButton("✅ SLOT 7")],
        [KeyboardButton("❌ Remove SLOT 1"), KeyboardButton("❌ Remove SLOT 2")],
        [KeyboardButton("❌ Remove SLOT 3"), KeyboardButton("❌ Remove SLOT 4")],
        [KeyboardButton("❌ Remove SLOT 5"), KeyboardButton("❌ Remove SLOT 6")],
        [KeyboardButton("❌ Remove SLOT 7")],
        [KeyboardButton("✅ Verify")],
        [KeyboardButton("❌ Remove Verify")],
        [KeyboardButton("📴 Set Offline Channel")],
        [KeyboardButton("❌ Remove Offline Channel")],
        [KeyboardButton("🧹 Clear Cache")],
        [KeyboardButton("🛡️ ADMIN PANEL")]
    ],
    resize_keyboard=True
)

user_states = {}

# ----------------- FORCE SUB CHECKER ----------------- #
async def check_force_sub(client, user_id):
    slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC")
    unjoined = []
    for slot in slots:
        s_id, chat_id, name, link = slot
        if link and link.strip():
            if chat_id and chat_id.strip():
                try:
                    member = await client.get_chat_member(chat_id.strip(), user_id)
                    if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                        unjoined.append((s_id, name or f"Channel {s_id}", link))
                except Exception:
                    unjoined.append((s_id, name or f"Channel {s_id}", link))
            else:
                unjoined.append((s_id, name or f"Channel {s_id}", link))
    return unjoined

# ----------------- SEND START LAYOUT ----------------- #
async def send_start_panel(client, message, user_id):
    if get_setting("bot_status") == "offline" and not is_admin(user_id):
        offline_chan = get_setting("offline_channel") or "https://t.me"
        return await message.reply_text(
            "🔴 **Bot is currently Offline for maintenance.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Official Channel ↗", url=offline_chan)]])
        )

    default_text = (
        "🔥 **Welcome SARKAR :: ⚔️ :: MOD**\n\n"
        "🚫 **Join All Channels To Unlock 📬**\n\n"
        "🚴‍♂️ 💧 **How To Get Key 💭📈**\n"
        "🧐 **GET KEY 🔔**"
    )
    custom_text = get_setting("promo_text") or default_text
    media_file = get_setting("media_file_id")
    media_type = get_setting("media_type")
    voice_file = get_setting("voice_file_id")

    # Build 2-Column Buttons Layout for Channels
    inline_buttons = []
    all_slots = get_db("SELECT id, name, link FROM slots ORDER BY id ASC")
    active_slots = [s for s in all_slots if s[2] and s[2].strip()]

    for i in range(0, len(active_slots), 2):
        row = []
        s1 = active_slots[i]
        row.append(InlineKeyboardButton(text=f"{s1[1] or f'Channel {s1[0]}'} ↗", url=s1[2]))
        if i + 1 < len(active_slots):
            s2 = active_slots[i+1]
            row.append(InlineKeyboardButton(text=f"{s2[1] or f'Channel {s2[0]}'} ↗", url=s2[2]))
        inline_buttons.append(row)

    click_name = get_setting("click_name")
    click_url = get_setting("click_url")
    if click_name and click_url:
        inline_buttons.append([InlineKeyboardButton(text=f"{click_name} ↗", url=click_url)])

    inline_buttons.append([InlineKeyboardButton(text="Check Joined ↗", callback_data="verify_sub")])

    markup = InlineKeyboardMarkup(inline_buttons)

    if media_type == "photo" and media_file:
        await client.send_photo(message.chat.id, photo=media_file, caption=custom_text, reply_markup=markup)
    elif media_type == "video" and media_file:
        await client.send_video(message.chat.id, video=media_file, caption=custom_text, reply_markup=markup)
    else:
        await client.send_message(message.chat.id, text=custom_text, reply_markup=markup)

    if voice_file:
        await client.send_voice(message.chat.id, voice=voice_file)

# ----------------- COMMAND HANDLERS ----------------- #
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    get_db("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,), commit=True)
    user_states.pop(user_id, None)
    await send_start_panel(client, message, user_id)

@app.on_message(filters.command("admin"))
async def admin_cmd(client, message: Message):
    user_id = message.from_user.id
    if is_owner(user_id):
        await message.reply_text("👑 **OWNER CONTROL PANEL ACTIVE**", reply_markup=OWNER_KEYBOARD)
    elif is_admin(user_id):
        await message.reply_text("🛡️ **ADMIN CONTROL PANEL ACTIVE**", reply_markup=ADMIN_KEYBOARD)
    else:
        await message.reply_text("❌ Access Denied")

@app.on_callback_query(filters.regex("verify_sub"))
async def verify_cb(client, callback):
    user_id = callback.from_user.id
    unjoined = await check_force_sub(client, user_id)
    if unjoined:
        await callback.answer("❌ Aapne abhi tak saare channels join nahi kiye!", show_alert=True)
    else:
        await callback.answer("✅ Verified Successfully!", show_alert=False)
        await callback.message.delete()
        await client.send_message(callback.message.chat.id, "🎉 **SUCCESS! All channels verified.**")

# ----------------- CONTROL BUTTON LOGIC ----------------- #
@app.on_message(filters.private & ~filters.command(["start", "admin"]))
async def handle_control_buttons(client, message: Message):
    user_id = message.from_user.id
    text = message.text or ""
    state = user_states.get(user_id)

    if not is_admin(user_id):
        return

    # OWNER ACTIONS
    if is_owner(user_id):
        if text == "➕ Add Admin":
            user_states[user_id] = "ADD_ADMIN"
            return await message.reply_text("👤 Send Telegram User ID of new Admin:")
        elif text == "❌ Remove Admin":
            user_states[user_id] = "DEL_ADMIN"
            return await message.reply_text("🗑️ Send Telegram User ID to remove Admin:")
        elif text == "📋 Admin List":
            admins = get_db("SELECT user_id FROM admins")
            ad_list = "\n".join([f"• `{a[0]}`" for a in admins]) or "No admins added."
            return await message.reply_text(f"📋 **ADMIN LIST:**\n\nOwner: `{OWNER_ID}`\n\n{ad_list}")
        elif text == "🗑️ Clear Stats User":
            get_db("DELETE FROM users", commit=True)
            return await message.reply_text("✅ All user stats cleared!")
        elif text == "📢 Broadcast":
            user_states[user_id] = "BROADCAST"
            return await message.reply_text("📢 Send broadcast message:")

    # SHARED ACTIONS
    if text in ["👑 OWNER PANEL", "🛡️ ADMIN PANEL"]:
        kb = OWNER_KEYBOARD if is_owner(user_id) else ADMIN_KEYBOARD
        return await message.reply_text("✅ Panel refreshed.", reply_markup=kb)

    elif text == "👥 Stats User":
        count = get_db("SELECT COUNT(*) FROM users", one=True)[0]
        return await message.reply_text(f"👥 **Total Users:** `{count}`")

    elif text == "❌ Bot Offline":
        set_setting("bot_status", "offline")
        return await message.reply_text("❌ Bot is now **Offline**.")

    elif text == "✅ Bot Online":
        set_setting("bot_status", "online")
        return await message.reply_text("✅ Bot is now **Online**.")

    elif text == "🚀 Start Bot":
        await send_start_panel(client, message, user_id)

    elif text == "✏️ Set Text Promo":
        user_states[user_id] = "SET_PROMO"
        return await message.reply_text("✏️ Send new Promo Text for `/start`:")

    elif text == "❌ Remove Promo Text":
        set_setting("promo_text", None)
        return await message.reply_text("✅ Promo text reset to default.")

    elif text == "🖼️ Set DP":
        user_states[user_id] = "SET_DP"
        return await message.reply_text("🖼️ Send Banner **Photo** or **Video**:")

    elif text == "❌ Remove DP":
        set_setting("media_type", None)
        set_setting("media_file_id", None)
        return await message.reply_text("✅ Banner DP/Video removed.")

    elif text == "🔗 Set Click Here":
        user_states[user_id] = "SET_CLICK"
        return await message.reply_text("🔗 Send format: `Button Name | https://link.com`")

    elif text == "❌ Remove Click Here Link":
        set_setting("click_name", None)
        set_setting("click_url", None)
        return await message.reply_text("✅ Custom Click Link removed.")

    elif text == "🎙️ Set Voice":
        user_states[user_id] = "SET_VOICE"
        return await message.reply_text("🎙️ Record & send a **Voice Note**:")

    elif text == "❌ Remove Voice":
        set_setting("voice_file_id", None)
        return await message.reply_text("✅ Voice Note removed.")

    elif text.startswith("✅ SLOT "):
        slot_num = text.replace("✅ SLOT ", "").strip()
        user_states[user_id] = f"SET_SLOT_{slot_num}"
        return await message.reply_text(f"⚙️ Send Slot {slot_num} Link or Details:\n\n1. **Direct Link:** `https://t.me/+xyz` or `https://t.me/channelname`\n2. **Full Format:** `ChatID | Channel Name | Link`")

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

    # STATE INPUT PROCESSOR
    if state == "ADD_ADMIN" and is_owner(user_id):
        try:
            aid = int(text.strip())
            get_db("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (aid,), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(f"✅ Admin `{aid}` Added!")
        except Exception:
            return await message.reply_text("❌ Send numeric User ID!")

    elif state == "DEL_ADMIN" and is_owner(user_id):
        try:
            aid = int(text.strip())
            get_db("DELETE FROM admins WHERE user_id=?", (aid,), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(f"✅ Admin `{aid}` Removed!")
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

    elif state == "SET_CLICK":
        try:
            p = [x.strip() for x in text.split("|")]
            set_setting("click_name", p[0])
            set_setting("click_url", p[1])
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Custom Link Updated!")
        except Exception:
            return await message.reply_text("❌ Format: `Name | https://link.com`")

    elif state == "SET_OFFLINE_CHAN":
        set_setting("offline_channel", text.strip())
        user_states.pop(user_id, None)
        return await message.reply_text("✅ Offline Channel Link Saved!")

    # FLEXIBLE SLOT PARSER (Direct link OR Full format)
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

        if "t.me" in link or "telegram.me" in link or "telegram.dog" in link:
            get_db("UPDATE slots SET chat_id=?, name=?, link=? WHERE id=?", (chat_id, name, link, slot_id), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(
                f"✅ **SLOT {slot_id} Saved Successfully!**\n\n"
                f"📌 **Name:** `{name}`\n"
                f"🆔 **ChatID:** `{chat_id or 'Auto/Direct Link'}`\n"
                f"🔗 **Link:** {link}"
            )
        else:
            return await message.reply_text("❌ Kripya valid Telegram link (`https://t.me/...`) bhejein!")

    elif state == "BROADCAST" and is_owner(user_id):
        users = get_db("SELECT user_id FROM users")
        s, f = 0, 0
        for u in users:
            try:
                await message.copy(u[0])
                s += 1
            except Exception:
                f += 1
        user_states.pop(user_id, None)
        return await message.reply_text(f"📢 **Broadcast Finished!**\n\n✅ Sent: `{s}`\n❌ Failed: `{f}`")

# ----------------- START BOT ----------------- #
if __name__ == "__main__":
    print("Bot Starting...")
    app.run()
