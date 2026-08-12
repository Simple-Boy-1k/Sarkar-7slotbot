import os
import sqlite3
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, Message
)
from pyrogram.errors import UserNotParticipant

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
    
    # Initialize default 7 empty slots if not created
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

def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    res = get_db("SELECT user_id FROM admins WHERE user_id=?", (user_id,), one=True)
    return bool(res)

# ----------------- ADMIN BOTTOM KEYBOARD ----------------- #
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("⚙️ Manage Slots (1-7)"), KeyboardButton("🖼️ Set DP/Video")],
        [KeyboardButton("🗑️ Remove DP/Video"), KeyboardButton("🎙️ Set Voice Note")],
        [KeyboardButton("🗑️ Remove Voice Note"), KeyboardButton("🔗 Set Click Link")],
        [KeyboardButton("🗑️ Remove Click Link"), KeyboardButton("✍️ Set Main Text")],
        [KeyboardButton("🔄 Reset Main Text"), KeyboardButton("👤 Add Admin")],
        [KeyboardButton("🗑️ Del Admin"), KeyboardButton("📊 Stats")],
        [KeyboardButton("📢 Broadcast")]
    ],
    resize_keyboard=True
)

# User states dictionary for step-by-step inputs
user_states = {}

# ----------------- FORCE SUB CHECKER ----------------- #
async def check_force_sub(client, user_id):
    slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC")
    unjoined = []
    for slot in slots:
        s_id, chat_id, name, link = slot
        if chat_id and chat_id.strip():
            try:
                member = await client.get_chat_member(chat_id.strip(), user_id)
                if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                    unjoined.append((name or f"Slot {s_id}", link))
            except Exception:
                unjoined.append((name or f"Slot {s_id}", link))
    return unjoined

# ----------------- SEND VERIFIED / START BANNER ----------------- #
async def send_welcome_content(client, message, user_id):
    media_type = get_setting("media_type")
    media_id = get_setting("media_file_id")
    voice_id = get_setting("voice_file_id")
    custom_text = get_setting("custom_text") or "🎉 **SUCCESS! ALL CHANNELS VERIFIED!**\n\nWelcome to the official panel."
    click_name = get_setting("click_btn_name")
    click_url = get_setting("click_btn_url")

    # Inline Click Button (if configured)
    inline_markup = None
    if click_name and click_url:
        inline_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text=click_name, url=click_url)]])

    # Bottom Reply Keyboard for Admin
    reply_box = ADMIN_KEYBOARD if is_admin(user_id) else None

    # Send Banner Photo / Video if set
    if media_type == "photo" and media_id:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=media_id,
            caption=custom_text,
            reply_markup=inline_markup
        )
    elif media_type == "video" and media_id:
        await client.send_video(
            chat_id=message.chat.id,
            video=media_id,
            caption=custom_text,
            reply_markup=inline_markup
        )
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text=custom_text,
            reply_markup=inline_markup
        )

    # Send Voice Note if set
    if voice_id:
        await client.send_voice(chat_id=message.chat.id, voice=voice_id)

    # Show Admin Bottom Keyboard if User is Admin
    if is_admin(user_id):
        await client.send_message(
            chat_id=message.chat.id,
            text="👑 **ADMIN CONTROL PANEL ACTIVE** (Niche keyboard box me options hain)",
            reply_markup=reply_box
        )

# ----------------- START COMMAND ----------------- #
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    get_db("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,), commit=True)
    user_states.pop(user_id, None)

    unjoined = await check_force_sub(client, user_id)

    if unjoined:
        buttons = []
        for name, link in unjoined:
            buttons.append([InlineKeyboardButton(text=f"📌 Join {name}", url=link)])
        buttons.append([InlineKeyboardButton(text="✅ VERIFY / JOINED", callback_data="verify_sub")])

        await message.reply_text(
            "⚠️ **Aapko pehle humare sabhi channels join karne honge!**\n\nNiche diye gaye buttons par click karke join karein aur 'VERIFY' dabayein:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await send_welcome_content(client, message, user_id)

# ----------------- VERIFY CALLBACK ----------------- #
@app.on_callback_query(filters.regex("verify_sub"))
async def verify_cb(client, callback):
    user_id = callback.from_user.id
    unjoined = await check_force_sub(client, user_id)

    if unjoined:
        await callback.answer("❌ Aapne abhi tak saare channels join nahi kiye!", show_alert=True)
    else:
        await callback.message.delete()
        await send_welcome_content(client, callback.message, user_id)

# ----------------- ADMIN COMMAND ----------------- #
@app.on_message(filters.command("admin"))
async def admin_cmd(client, message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return await message.reply_text("❌ Aap admin nahi hain!")
    
    await message.reply_text(
        "👑 **FULL ADMIN CONTROL PANEL**\n\nNiche box keyboard me se option select karein:",
        reply_markup=ADMIN_KEYBOARD
    )

# ----------------- REPLIES & BUTTON HANDLERS ----------------- #
@app.on_message(filters.private & ~filters.command(["start", "admin"]))
async def handle_admin_inputs(client, message: Message):
    user_id = message.from_user.id
    text = message.text or ""
    state = user_states.get(user_id)

    if not is_admin(user_id):
        return

    # --- ADMIN KEYBOARD BUTTON PRESSES ---
    if text == "⚙️ Manage Slots (1-7)":
        user_states[user_id] = "WAITING_SLOT_INPUT"
        slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC")
        msg = "⚙️ **CURRENT SLOTS CONFIG:**\n\n"
        for s in slots:
            msg += f"Slot {s[0]}: Name=`{s[2]}` | ChatID=`{s[1]}` | Link=`{s[3]}`\n"
        msg += "\nSlot update karne ke liye is format me bhejein:\n`SlotNumber | ChatID | ChannelName | ChannelLink`\n*(Example: `1 | -100123456789 | MyChannel | https://t.me/MyChannel`)*"
        return await message.reply_text(msg)

    elif text == "🖼️ Set DP/Video":
        user_states[user_id] = "WAITING_MEDIA"
        return await message.reply_text("🖼️ Abhi Bot Banner ke liye **Photo** ya **Video** bhejein:")

    elif text == "🗑️ Remove DP/Video":
        set_setting("media_type", None)
        set_setting("media_file_id", None)
        return await message.reply_text("✅ DP / Video Banner successfully remove ho gaya!")

    elif text == "🎙️ Set Voice Note":
        user_states[user_id] = "WAITING_VOICE"
        return await message.reply_text("🎙️ Abhi **Voice Note** record karke bhejein:")

    elif text == "🗑️ Remove Voice Note":
        set_setting("voice_file_id", None)
        return await message.reply_text("✅ Voice Note successfully remove ho gaya!")

    elif text == "🔗 Set Click Link":
        user_states[user_id] = "WAITING_CLICK_LINK"
        return await message.reply_text("🔗 Custom Button lagane ke liye format me bhejein:\n`Button Text | https://t.me/yourlink`")

    elif text == "🗑️ Remove Click Link":
        set_setting("click_btn_name", None)
        set_setting("click_btn_url", None)
        return await message.reply_text("✅ Custom Click Button remove ho gaya!")

    elif text == "✍️ Set Main Text":
        user_states[user_id] = "WAITING_MAIN_TEXT"
        return await message.reply_text("✍️ Verified users ke liye naya **Welcome Message** bhejein:")

    elif text == "🔄 Reset Main Text":
        set_setting("custom_text", None)
        return await message.reply_text("✅ Main Text default reset ho gaya!")

    elif text == "👤 Add Admin":
        user_states[user_id] = "WAITING_ADD_ADMIN"
        return await message.reply_text("👤 Naye Admin ka **Telegram User ID** bhejein:")

    elif text == "🗑️ Del Admin":
        user_states[user_id] = "WAITING_DEL_ADMIN"
        return await message.reply_text("🗑️ Remove karne ke liye Admin ka **Telegram User ID** bhejein:")

    elif text == "📊 Stats":
        total_users = get_db("SELECT COUNT(*) FROM users", one=True)[0]
        return await message.reply_text(f"📊 **TOTAL BOT USERS:** `{total_users}`")

    elif text == "📢 Broadcast":
        user_states[user_id] = "WAITING_BROADCAST"
        return await message.reply_text("📢 Sabhi users ko broadcast karne ke liye **Message** bhejein:")

    # --- PROCESS INPUT STATES ---
    if state == "WAITING_MEDIA":
        if message.photo:
            set_setting("media_type", "photo")
            set_setting("media_file_id", message.photo.file_id)
            user_states.pop(user_id, None)
            return await message.reply_text("✅ DP Photo Banner Updated Successfully!")
        elif message.video:
            set_setting("media_type", "video")
            set_setting("media_file_id", message.video.file_id)
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Video Banner Updated Successfully!")
        else:
            return await message.reply_text("❌ Kripya photo ya video hi bhejein!")

    elif state == "WAITING_VOICE":
        if message.voice:
            set_setting("voice_file_id", message.voice.file_id)
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Voice Note Set Successfully!")
        else:
            return await message.reply_text("❌ Kripya Voice Note hi bhejein!")

    elif state == "WAITING_SLOT_INPUT":
        try:
            parts = [p.strip() for p in text.split("|")]
            slot_num, chat_id, name, link = int(parts[0]), parts[1], parts[2], parts[3]
            get_db("INSERT OR REPLACE INTO slots (id, chat_id, name, link) VALUES (?, ?, ?, ?)", (slot_num, chat_id, name, link), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(f"✅ Slot {slot_num} updated successfully!")
        except Exception:
            return await message.reply_text("❌ Invalid Format! Format: `1 | -100xxx | Name | Link`")

    elif state == "WAITING_CLICK_LINK":
        try:
            parts = [p.strip() for p in text.split("|")]
            set_setting("click_btn_name", parts[0])
            set_setting("click_btn_url", parts[1])
            user_states.pop(user_id, None)
            return await message.reply_text("✅ Custom Click Button Updated!")
        except Exception:
            return await message.reply_text("❌ Invalid Format! Use: `Button Name | Link`")

    elif state == "WAITING_MAIN_TEXT":
        set_setting("custom_text", text)
        user_states.pop(user_id, None)
        return await message.reply_text("✅ Main Text Updated!")

    elif state == "WAITING_ADD_ADMIN":
        try:
            new_admin = int(text.strip())
            get_db("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin,), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(f"✅ Admin `{new_admin}` Added Successfully!")
        except Exception:
            return await message.reply_text("❌ Sahi Numeric User ID bhejein!")

    elif state == "WAITING_DEL_ADMIN":
        try:
            del_admin = int(text.strip())
            get_db("DELETE FROM admins WHERE user_id=?", (del_admin,), commit=True)
            user_states.pop(user_id, None)
            return await message.reply_text(f"✅ Admin `{del_admin}` Removed Successfully!")
        except Exception:
            return await message.reply_text("❌ Sahi Numeric User ID bhejein!")

    elif state == "WAITING_BROADCAST":
        users = get_db("SELECT user_id FROM users")
        success, failed = 0, 0
        await message.reply_text("📢 Broadcasting Started...")
        for u in users:
            try:
                await message.copy(chat_id=u[0])
                success += 1
            except Exception:
                failed += 1
        user_states.pop(user_id, None)
        return await message.reply_text(f"📢 **BROADCAST COMPLETE!**\n\n✅ Success: `{success}`\n❌ Failed: `{failed}`")

# ----------------- RUN BOT ----------------- #
if __name__ == "__main__":
    print("Bot Starting...")
    app.run()
