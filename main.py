import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from database import init_db, get_db, get_setting, is_admin
from admin import setup_admin_handlers, user_states
import emojis

# Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

app = Client("Sarkar_7Slot_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
init_db()

# ----------------- URL CLEANER -----------------
def clean_url(url):
    if not url:
        return None
    url = str(url).strip()
    if not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("t.me/") or url.startswith("tg://")):
        url = f"https://{url}"
    return url

# ----------------- GLOBAL PRE-BUILT RAM CACHE -----------------
START_CACHE = {
    "status": "online",
    "offline_markup": None,
    "media_file": None,
    "media_type": None,
    "voice_file": None,
    "markup": None,
    "caption_template": "",
    "slots": []
}

def build_start_cache():
    """ Runs once at startup & updates in RAM for ZERO delay on /start """
    global START_CACHE
    
    status = get_setting("bot_status") or "online"
    offline_chan = clean_url(get_setting("offline_channel")) or "https://t.me"
    offline_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Official Channel", url=offline_chan)]])

    raw_key = get_setting("get_key_url")
    raw_click = get_setting("click_url")
    get_key_link = clean_url(raw_click if (raw_click and str(raw_click).strip()) else raw_key)
    has_key_link = bool(get_key_link)

    header = f"{emojis.EMOJI_WELCOME_HEAD} <b>Welcome {{name}} 🌹</b>\n\n"
    
    if has_key_link:
        indent = "\u00A0" * 8
        footer = (
            f"\n\n{emojis.EMOJI_KEY_HEAD_LEFT1} {emojis.EMOJI_KEY_HEAD_LEFT2} <b>𝐇𝐨𝐰 𝐓𝐨 𝐆𝐞𝐭 𝐊𝐞𝐲</b> {emojis.EMOJI_KEY_HEAD_RIGHT1} {emojis.EMOJI_KEY_HEAD_RIGHT2}\n"
            f"{indent}{emojis.EMOJI_GET_KEY_LEFT} <a href='{get_key_link}'><b>𝐆𝐞𝐭 𝐊𝐞𝐲 </b></a> {emojis.EMOJI_GET_KEY_RIGHT}"
        )
    else:
        footer = ""

    custom_text = get_setting("promo_text")

    if custom_text:
        formatted_text = str(custom_text)
        if has_key_link:
            formatted_text = formatted_text.replace("{key_link}", get_key_link)

        if "𝐆𝐞𝐭 𝐊𝐞𝐲" in custom_text or "𝐇𝐨𝐰 𝐓𝐨 𝐆𝐞𝐭 𝐊𝐞𝐲" in custom_text:
            caption_template = formatted_text
        else:
            caption_template = f"{header}{formatted_text}{footer}"
    else:
        middle = "🚫 <b>𝐉𝐨𝐢𝐧 𝐀𝐥𝐥 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐓𝐨 𝐔𝐧𝐥𝐨𝐜𝐤 </b> 📬"
        caption_template = f"{header}{middle}{footer}"

    # Build Buttons Pre-hand
    all_slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC") or []
    active_slots = [s for s in all_slots if isinstance(s, (list, tuple)) and len(s) >= 4 and s[3] and str(s[3]).strip()]

    inline_buttons = []
    for i in range(0, len(active_slots), 2):
        row = []
        s1 = active_slots[i]
        s1_name = s1[2] if len(s1) > 2 and s1[2] else f"Channel {s1[0]}"
        s1_link = clean_url(s1[3])
        if s1_link:
            row.append(InlineKeyboardButton(text=f"💜 {s1_name}", url=s1_link))
        
        if i + 1 < len(active_slots):
            s2 = active_slots[i+1]
            s2_name = s2[2] if len(s2) > 2 and s2[2] else f"Channel {s2[0]}"
            s2_link = clean_url(s2[3])
            if s2_link:
                row.append(InlineKeyboardButton(text=f"💜 {s2_name}", url=s2_link))
            
        if row:
            inline_buttons.append(row)

    verify_url = clean_url(get_setting("verify_url"))
    if verify_url:
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", url=verify_url)])
    else:
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", callback_data="verify_sub")])

    START_CACHE["status"] = status
    START_CACHE["offline_markup"] = offline_markup
    START_CACHE["media_file"] = get_setting("media_file_id")
    START_CACHE["media_type"] = get_setting("media_type")
    START_CACHE["voice_file"] = get_setting("voice_file_id")
    START_CACHE["markup"] = InlineKeyboardMarkup(inline_buttons) if inline_buttons else None
    START_CACHE["caption_template"] = caption_template
    START_CACHE["slots"] = active_slots

# Initialize cache at startup
build_start_cache()

# ----------------- PARALLEL FORCE SUB CHECK -----------------
async def _check_single_slot(client, slot, user_id):
    if not isinstance(slot, (list, tuple)) or len(slot) < 4:
        return None
    s_id, chat_id, name, link = slot[0], slot[1], slot[2], slot[3]
    link = clean_url(link)
    if link and chat_id and str(chat_id).strip():
        try:
            member = await client.get_chat_member(str(chat_id).strip(), user_id)
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                return (s_id, name or f"Channel {s_id}", link)
        except Exception:
            return (s_id, name or f"Channel {s_id}", link)
    return None

async def check_force_sub(client, user_id):
    tasks = [_check_single_slot(client, slot, user_id) for slot in START_CACHE["slots"]]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res is not None]

# ----------------- LIGHTNING FAST START HANDLER -----------------
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    
    # Non-blocking DB save
    asyncio.create_task(asyncio.to_thread(get_db, "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,), True))
    user_states.pop(user_id, None)

    # Offline check
    if START_CACHE["status"] == "offline" and not is_admin(user_id, OWNER_ID):
        return await message.reply_text("🔴 <b>Bot is currently Offline for maintenance.</b>", reply_markup=START_CACHE["offline_markup"], parse_mode=enums.ParseMode.HTML)

    user = message.from_user
    first_name = user.first_name if user and user.first_name else "User"
    last_name = user.last_name if user and user.last_name else ""
    full_name = f"{first_name} {last_name}".strip()
    mention = user.mention if user else full_name

    # Quick dynamic name replacement (Nanoseconds)
    caption_text = START_CACHE["caption_template"].replace("{name}", full_name)\
                                                  .replace("{first_name}", first_name)\
                                                  .replace("{mention}", mention)

    chat_id = message.chat.id
    media_file = START_CACHE["media_file"]
    media_type = START_CACHE["media_type"]
    markup = START_CACHE["markup"]

    # INSTANT SEND
    if media_type == "photo" and media_file:
        await client.send_photo(chat_id, photo=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    elif media_type == "video" and media_file:
        await client.send_video(chat_id, video=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(chat_id, text=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    if START_CACHE["voice_file"]:
        await client.send_voice(chat_id, voice=START_CACHE["voice_file"])

@app.on_callback_query(filters.regex("verify_sub"))
async def verify_cb(client, callback: CallbackQuery):
    if START_CACHE["status"] == "offline" and not is_admin(callback.from_user.id, OWNER_ID):
        return await callback.answer("🔴 Bot is currently offline for maintenance!", show_alert=True)

    user_id = callback.from_user.id
    unjoined = await check_force_sub(client, user_id)
    if unjoined:
        await callback.answer("❌ Aapne abhi tak saare channels join nahi kiye!", show_alert=True)
    else:
        await callback.answer("✅ Verified Successfully!", show_alert=False)
        
        raw_key = get_setting("get_key_url")
        raw_click = get_setting("click_url")
        final_key_url = clean_url(raw_click if (raw_click and str(raw_click).strip()) else raw_key)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        if final_key_url:
            key_msg = f"🎉 <b>SUCCESS! All channels verified.</b>\n\n🔑 <b>Your Key Link:</b> {final_key_url}"
        else:
            key_msg = "🎉 <b>SUCCESS! All channels verified.</b>"
            
        await client.send_message(callback.message.chat.id, key_msg, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

# Function to refresh cache when Admin changes anything
async def send_start_panel_refresh(client, message, user_id):
    build_start_cache()
    await start_cmd(client, message)

setup_admin_handlers(app, OWNER_ID, send_start_panel_refresh)

if __name__ == "__main__":
    print("🚀 Pre-Built Fast Engine Starting...")
    app.run()
