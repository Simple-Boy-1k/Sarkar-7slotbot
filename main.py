import os
import sqlite3
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
)
from pyrogram.errors import (
    UserNotParticipant, ChatAdminRequired, ChannelInvalid, PeerIdInvalid
)

# Configs (Heroku Environment Variables)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

app = Client("full_control_fsub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= DATABASE SETUP =================
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()

# Table for 7 Slots
cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    slot_id INTEGER PRIMARY KEY,
    chat_id TEXT,
    name TEXT,
    link TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

# Settings Helper Functions
def get_setting(key, default=""):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def set_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()

def del_setting(key):
    cursor.execute("DELETE FROM settings WHERE key=?", (key,))
    conn.commit()

# Ensure Owner is Admin
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (OWNER_ID,))
conn.commit()

def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    cursor.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def add_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ================= FSUB CHECKING ENGINE =================
async def check_all_7_channels(client: Client, user_id: int) -> bool:
    if is_admin(user_id):
        return True
        
    cursor.execute("SELECT chat_id FROM channels WHERE chat_id IS NOT NULL AND chat_id != ''")
    rows = cursor.fetchall()
    
    if not rows:
        return True

    for (chat_target,) in rows:
        try:
            target = int(chat_target) if (chat_target.startswith("-100") or chat_target.lstrip("-").isdigit()) else chat_target
            member = await client.get_chat_member(target, user_id)
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.RESTRICTED, enums.ChatMemberStatus.LEFT]:
                return False
        except UserNotParticipant:
            return False
        except (ChatAdminRequired, ChannelInvalid, PeerIdInvalid):
            continue
        except Exception:
            continue
    return True

def build_user_keyboard():
    cursor.execute("SELECT slot_id, name, link FROM channels ORDER BY slot_id ASC")
    slots = cursor.fetchall()
    
    emojis = ["💜", "⚡", "🔥", "🚀", "👑", "💎", "🎯"]
    slot_dict = {s[0]: s for s in slots}
    
    buttons = []
    row1, row2, row3 = [], [], []
    
    # Active Channels Keyboard Grid (Slot 1 to 7)
    for i in range(1, 8):
        emoji = emojis[(i - 1) % len(emojis)]
        if i in slot_dict and slot_dict[i][1] and slot_dict[i][2]:
            btn_text = f"{emoji} {slot_dict[i][1]}"
            btn_url = slot_dict[i][2]
            btn = InlineKeyboardButton(btn_text, url=btn_url)
            
            if i in [1, 2]:
                row1.append(btn)
            elif i in [3, 4]:
                row2.append(btn)
            elif i in [5, 6]:
                row3.append(btn)
            elif i == 7:
                row3.append(btn)

    if row1: buttons.append(row1)
    if row2: buttons.append(row2)
    if row3: buttons.append(row3)

    # Click Here Button (If enabled by admin)
    click_link = get_setting("click_here_link", "")
    click_text = get_setting("click_here_text", "👉 Click Here")
    if click_link:
        buttons.append([InlineKeyboardButton(click_text, url=click_link)])

    # Always present Verify Button
    buttons.append([InlineKeyboardButton("✅ Check Joined", callback_data="check_joined_sub")])
    return InlineKeyboardMarkup(buttons)

# ================= USER /START HANDLER =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    add_user(user_id)
    
    is_joined = await check_all_7_channels(client, user_id)
    
    if is_joined:
        await send_unlocked_panel(message)
    else:
        start_text = get_setting("start_text", (
            f"🔥 <b>Welcome {message.from_user.first_name}!</b>\n\n"
            f"🚫 <b>Join All Channels To Unlock Access</b> 🌐\n\n"
            f"👇 <i>Neeche diye gaye sabhi channels join karke 'Check Joined' par click karein.</i>"
        ))
        
        media_type = get_setting("media_type", "")
        media_id = get_setting("media_id", "")
        voice_id = get_setting("voice_id", "")
        
        # 1. Voice Note (If set)
        if voice_id:
            try:
                await message.reply_voice(voice=voice_id)
            except Exception:
                pass

        # 2. DP/Video Banner or Text + Inline Buttons
        keyboard = build_user_keyboard()
        if media_type == "photo" and media_id:
            try:
                await message.reply_photo(photo=media_id, caption=start_text, reply_markup=keyboard)
                return
            except Exception:
                pass
        elif media_type == "video" and media_id:
            try:
                await message.reply_video(video=media_id, caption=start_text, reply_markup=keyboard)
                return
            except Exception:
                pass
                
        await message.reply_text(text=start_text, reply_markup=keyboard)

# Verify Callback
@app.on_callback_query(filters.regex("check_joined_sub"))
async def verify_cb(client: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    is_joined = await check_all_7_channels(client, user_id)
    
    if not is_joined:
        await cb.answer("❌ Aapne saare channels join nahi kiye! Pehle join karein.", show_alert=True)
        return
        
    await cb.answer("✅ Verified Successfully!")
    
    success_text = get_setting("success_text", "🎉 <b>SUCCESS! ALL CHANNELS VERIFIED!</b>\n\nWelcome to the official panel.")
    
    if cb.message.photo or cb.message.video:
        await cb.message.edit_caption(caption=success_text)
    else:
        await cb.message.edit_text(text=success_text)

async def send_unlocked_panel(message: Message):
    success_text = get_setting("success_text", "🎉 <b>SUCCESS! ALL CHANNELS VERIFIED!</b>\n\nWelcome to the official panel.")
    await message.reply_text(success_text)

# ================= ADMIN CONTROL PANEL =================
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
        
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Manage Slots (1-7)", callback_data="admin_manage_slots")
        ],
        [
            InlineKeyboardButton("🖼️ Set DP/Video", callback_data="admin_set_media"),
            InlineKeyboardButton("🗑️ Remove DP/Video", callback_data="admin_del_media")
        ],
        [
            InlineKeyboardButton("🎙️ Set Voice Note", callback_data="admin_set_voice"),
            InlineKeyboardButton("🗑️ Remove Voice Note", callback_data="admin_del_voice")
        ],
        [
            InlineKeyboardButton("🔗 Set Click Link", callback_data="admin_set_click_link"),
            InlineKeyboardButton("🗑️ Remove Click Link", callback_data="admin_del_click_link")
        ],
        [
            InlineKeyboardButton("✍️ Set Main Text", callback_data="admin_set_text"),
            InlineKeyboardButton("🔄 Reset Main Text", callback_data="admin_reset_text")
        ],
        [
            InlineKeyboardButton("👤 Add Admin", callback_data="admin_add_admin"),
            InlineKeyboardButton("🗑️ Del Admin", callback_data="admin_del_admin")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ]
    ])
    
    await message.reply_text("👑 <b>FULL ADMIN CONTROL PANEL (SET & REMOVE)</b>\n\nChoose an option to edit or reset:", reply_markup=buttons)

ADMIN_STEPS = {}

@app.on_callback_query(filters.regex("^admin_"))
async def admin_callbacks(client: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    if not is_admin(user_id):
        await cb.answer("❌ Access Denied!", show_alert=True)
        return

    data = cb.data

    # Channel Slot Management
    if data == "admin_manage_slots":
        cursor.execute("SELECT slot_id, name FROM channels")
        active_slots = {row[0]: row[1] for row in cursor.fetchall()}
        
        buttons = []
        for slot in range(1, 8):
            status = f"✅ ({active_slots[slot]})" if slot in active_slots else "❌ Empty"
            buttons.append([
                InlineKeyboardButton(f"Slot {slot}: {status}", callback_data=f"view_slot_{slot}")
            ])
        buttons.append([InlineKeyboardButton("« Back to Admin Panel", callback_data="admin_back")])
        await cb.message.edit_text("Select a Slot (1 to 7) to Set or Clear:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_back":
        await admin_panel(client, cb.message)

    # Set / Remove DP & Video Banner
    elif data == "admin_set_media":
        ADMIN_STEPS[user_id] = "set_media"
        await cb.message.reply_text("🖼️ Send Photo ya Video jise Bot Banner banana hai:")

    elif data == "admin_del_media":
        del_setting("media_type")
        del_setting("media_id")
        await cb.answer("✅ DP/Video Banner Removed!", show_alert=True)

    # Set / Remove Voice Note
    elif data == "admin_set_voice":
        ADMIN_STEPS[user_id] = "set_voice"
        await cb.message.reply_text("🎙️ Send Voice Note jise /start par play karna hai:")

    elif data == "admin_del_voice":
        del_setting("voice_id")
        await cb.answer("✅ Voice Note Removed!", show_alert=True)

    # Set / Remove Click Here Link
    elif data == "admin_set_click_link":
        ADMIN_STEPS[user_id] = "set_click_link"
        await cb.message.reply_text(
            "🔗 Send Click Link details in format:\n"
            "<code>Button Name|URL</code>\n\n"
            "<b>Example:</b>\n"
            "<code>👉 Click Here|https://t.me/SARKAR_MODS</code>"
        )

    elif data == "admin_del_click_link":
        del_setting("click_here_text")
        del_setting("click_here_link")
        await cb.answer("✅ Click Here Link Button Removed!", show_alert=True)

    # Set / Reset Main Text
    elif data == "admin_set_text":
        ADMIN_STEPS[user_id] = "set_text"
        await cb.message.reply_text("✍️ Send new <b>Main Text</b> for /start:")

    elif data == "admin_reset_text":
        del_setting("start_text")
        await cb.answer("✅ Main Text Reset to Default!", show_alert=True)

    # Add / Remove Admin
    elif data == "admin_add_admin":
        if user_id != OWNER_ID:
            await cb.answer("Only Owner can add admins!", show_alert=True)
            return
        ADMIN_STEPS[user_id] = "add_admin"
        await cb.message.reply_text("👤 Send Telegram <b>User ID</b> of new Admin:")

    elif data == "admin_del_admin":
        if user_id != OWNER_ID:
            await cb.answer("Only Owner can remove admins!", show_alert=True)
            return
        cursor.execute("SELECT user_id FROM admins WHERE user_id != ?", (OWNER_ID,))
        admins = cursor.fetchall()
        if not admins:
            await cb.answer("No secondary admins found!", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"❌ {uid}", callback_data=f"deladm_{uid}")] for (uid,) in admins]
        buttons.append([InlineKeyboardButton("« Back", callback_data="admin_back")])
        await cb.message.edit_text("Select Admin to remove:", reply_markup=InlineKeyboardMarkup(buttons))

    # Stats & Broadcast
    elif data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        await cb.answer(f"📊 Total Users: {total_users}", show_alert=True)

    elif data == "admin_broadcast":
        ADMIN_STEPS[user_id] = "broadcast"
        await cb.message.reply_text("📢 Send message to Broadcast:")

# Individual Slot Menu (Set / Clear)
@app.on_callback_query(filters.regex("^view_slot_"))
async def view_slot_cb(client: Client, cb: CallbackQuery):
    slot_num = int(cb.data.replace("view_slot_", ""))
    cursor.execute("SELECT name, link, chat_id FROM channels WHERE slot_id=?", (slot_num,))
    row = cursor.fetchone()

    if row:
        info = f"📢 <b>Slot {slot_num} Configured:</b>\nName: {row[0]}\nLink: {row[1]}\nChat ID: {row[2]}"
    else:
        info = f"📢 <b>Slot {slot_num} is currently Empty.</b>"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✏️ Set / Edit Slot {slot_num}", callback_data=f"edit_slot_btn_{slot_num}")],
        [InlineKeyboardButton(f"🗑️ Clear / Remove Slot {slot_num}", callback_data=f"clear_slot_btn_{slot_num}")],
        [InlineKeyboardButton("« Back to Slots", callback_data="admin_manage_slots")]
    ])
    await cb.message.edit_text(info, reply_markup=buttons)

@app.on_callback_query(filters.regex("^edit_slot_btn_"))
async def edit_slot_click(client: Client, cb: CallbackQuery):
    slot_num = int(cb.data.replace("edit_slot_btn_", ""))
    ADMIN_STEPS[cb.from_user.id] = f"edit_slot_{slot_num}"
    await cb.message.reply_text(
        f"📢 Send details for <b>Slot {slot_num}</b> in format:\n"
        f"<code>ChatID|ButtonName|InviteLink</code>\n\n"
        f"<b>Example:</b>\n"
        f"<code>-1001234567890|Channel {slot_num}|https://t.me/SARKAR_MODS</code>"
    )

@app.on_callback_query(filters.regex("^clear_slot_btn_"))
async def clear_slot_click(client: Client, cb: CallbackQuery):
    slot_num = int(cb.data.replace("clear_slot_btn_", ""))
    cursor.execute("DELETE FROM channels WHERE slot_id=?", (slot_num,))
    conn.commit()
    await cb.answer(f"✅ Slot {slot_num} Removed!", show_alert=True)
    await admin_callbacks(client, cb)

@app.on_callback_query(filters.regex("^deladm_"))
async def del_adm_cb(client: Client, cb: CallbackQuery):
    uid = int(cb.data.replace("deladm_", ""))
    cursor.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    conn.commit()
    await cb.answer("✅ Admin Removed!", show_alert=True)
    await admin_panel(client, cb.message)

# Handle Admin Text / Media Inputs
@app.on_message(filters.private & ~filters.command(["start", "admin"]))
async def handle_admin_inputs(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_STEPS or not is_admin(user_id):
        return

    step = ADMIN_STEPS.pop(user_id)

    if step.startswith("edit_slot_"):
        slot_num = int(step.replace("edit_slot_", ""))
        try:
            parts = message.text.strip().split("|")
            chat_id, name, link = parts[0].strip(), parts[1].strip(), parts[2].strip()
            cursor.execute("INSERT OR REPLACE INTO channels (slot_id, chat_id, name, link) VALUES (?, ?, ?, ?)", (slot_num, chat_id, name, link))
            conn.commit()
            await message.reply_text(f"✅ <b>Slot {slot_num}</b> updated with channel <b>{name}</b>!")
        except Exception:
            await message.reply_text("❌ Invalid Format! Use: <code>ChatID|ButtonName|InviteLink</code>")

    elif step == "set_media":
        if message.photo:
            set_setting("media_type", "photo")
            set_setting("media_id", message.photo.file_id)
            await message.reply_text("✅ DP Photo Banner Updated!")
        elif message.video:
            set_setting("media_type", "video")
            set_setting("media_id", message.video.file_id)
            await message.reply_text("✅ Video Banner Updated!")
        else:
            await message.reply_text("❌ Send Photo or Video only!")

    elif step == "set_voice":
        if message.voice:
            set_setting("voice_id", message.voice.file_id)
            await message.reply_text("✅ Voice Note Updated!")
        else:
            await message.reply_text("❌ Send a Voice Message only!")

    elif step == "set_click_link":
        try:
            parts = message.text.strip().split("|")
            click_text, click_link = parts[0].strip(), parts[1].strip()
            set_setting("click_here_text", click_text)
            set_setting("click_here_link", click_link)
            await message.reply_text(f"✅ Click Button Updated: <b>{click_text}</b> -> {click_link}")
        except Exception:
            await message.reply_text("❌ Format: <code>Button Name|URL</code>")

    elif step == "set_text":
        set_setting("start_text", message.text.html)
        await message.reply_text("✅ Main Start Text Updated!")

    elif step == "add_admin":
        if message.text.isdigit():
            new_admin = int(message.text)
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin,))
            conn.commit()
            await message.reply_text(f"✅ User <code>{new_admin}</code> added as Admin!")
        else:
            await message.reply_text("❌ Invalid User ID!")

    elif step == "broadcast":
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        success = 0
        status_msg = await message.reply_text("🔄 Broadcasting message...")
        for (uid,) in users:
            try:
                await message.copy(uid)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        await status_msg.edit_text(f"📢 Broadcast Finished!\n\n✅ Sent to: {success} users")

if __name__ == "__main__":
    print("Full Control 7-Slot Bot Started!")
    app.run()

