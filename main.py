import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from database import init_db, get_db, get_setting, is_admin
from admin import setup_admin_handlers, user_states
from start_logger import notify_owner_on_start
from start_panel import get_colored_start_panel, clean_url

# Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

app = Client("Sarkar_7Slot_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
init_db()

# =========================================================
# TELEGRAM PREMIUM EMOJI IDs & HELPER SETUP
# =========================================================
ID_WELCOME_HEAD     = "6077883305187876926"  # 🔥 Welcome se pehle
ID_KEY_HEAD_LEFT1   = "6269194596094317437"  # 🟢 How To Get Key ke left me pehla
ID_KEY_HEAD_LEFT2   = "6079974593483775722"  # ⚡ How To Get Key ke left me doosra
ID_KEY_HEAD_RIGHT1  = "6237552274944564087"  # 💨 How To Get Key ke right me pehla
ID_KEY_HEAD_RIGHT2  = "6244425785986257276"  # 📈 How To Get Key ke right me doosra
ID_GET_KEY_LEFT     = "6010103971023166824"  # 🤫 GET KEY ke left me
ID_GET_KEY_RIGHT    = "6271271702408204490"  # 🔔 GET KEY ke right me

def get_emoji(emoji_id: str, fallback: str) -> str:
    if emoji_id and str(emoji_id).strip():
        return f'<emoji id="{emoji_id.strip()}">{fallback}</emoji>'
    return fallback

# Formatted Premium Emojis
EMOJI_WELCOME_HEAD    = get_emoji(ID_WELCOME_HEAD, "🔥")
EMOJI_KEY_HEAD_LEFT1  = get_emoji(ID_KEY_HEAD_LEFT1, "🟢")
EMOJI_KEY_HEAD_LEFT2  = get_emoji(ID_KEY_HEAD_LEFT2, "⚡")
EMOJI_KEY_HEAD_RIGHT1 = get_emoji(ID_KEY_HEAD_RIGHT1, "💨")
EMOJI_KEY_HEAD_RIGHT2 = get_emoji(ID_KEY_HEAD_RIGHT2, "📈")
EMOJI_GET_KEY_LEFT    = get_emoji(ID_GET_KEY_LEFT, "🤫")
EMOJI_GET_KEY_RIGHT   = get_emoji(ID_GET_KEY_RIGHT, "🔔")


# ----------------- LIGHTNING-FAST PARALLEL CAPTION BUILDER -----------------
async def get_caption_and_status_async(user_full_name):
    status_task = asyncio.to_thread(get_setting, "bot_status")
    offline_chan_task = asyncio.to_thread(get_setting, "offline_channel")
    raw_key_task = asyncio.to_thread(get_setting, "get_key_url")
    raw_click_task = asyncio.to_thread(get_setting, "click_url")
    custom_text_task = asyncio.to_thread(get_setting, "promo_text")

    status, offline_chan_raw, raw_key, raw_click, custom_text = await asyncio.gather(
        status_task, offline_chan_task, raw_key_task, raw_click_task, custom_text_task
    )

    status = status or "online"
    offline_chan = clean_url(offline_chan_raw) or "https://t.me"
    
    offline_btn_kwargs = {"text": "Official Channel", "url": offline_chan}
    if hasattr(enums, "ButtonStyle") and hasattr(enums.ButtonStyle, "PRIMARY"):
        offline_btn_kwargs["style"] = enums.ButtonStyle.PRIMARY

    offline_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(**offline_btn_kwargs)]
    ])

    get_key_link = clean_url(raw_click if (raw_click and str(raw_click).strip()) else raw_key)
    has_key_link = bool(get_key_link)

    header = f"{EMOJI_WELCOME_HEAD} <b>Welcome {user_full_name}</b>\n\n"
    
    if has_key_link:
        footer = (
            f"\n\n{EMOJI_KEY_HEAD_LEFT1}{EMOJI_KEY_HEAD_LEFT2} <b>𝐇𝐨𝐰 𝐓𝐨 𝐆𝐞𝐭 𝐊𝐞𝐲</b> {EMOJI_KEY_HEAD_RIGHT1}{EMOJI_KEY_HEAD_RIGHT2}\n"
            f"{EMOJI_GET_KEY_LEFT} <a href='{get_key_link}'><b>𝐆𝐄𝐓 𝐊𝐄𝐘</b></a> {EMOJI_GET_KEY_RIGHT}"
        )
    else:
        footer = ""

    if custom_text:
        formatted_text = str(custom_text)
        if has_key_link:
            formatted_text = formatted_text.replace("{key_link}", get_key_link)

        if "GET KEY" in custom_text or "How To Get Key" in custom_text or "𝐆𝐞𝐭 𝐊𝐞𝐲" in custom_text:
            caption_text = formatted_text
        else:
            caption_text = f"{header}{formatted_text}{footer}"
    else:
        middle = "🚫 <b>Join All Channels To Unlock</b> 📬"
        caption_text = f"{header}{middle}{footer}"

    return status, offline_markup, caption_text

# ----------------- PARALLEL FAST FORCE SUB CHECK -----------------
async def _check_single_slot(client, slot, user_id):
    s_id, chat_id, name, link = slot[0], slot[1], slot[2], slot[3]
    if chat_id and str(chat_id).strip():
        try:
            member = await client.get_chat_member(str(chat_id).strip(), user_id)
            if member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
                return (s_id, name or f"Channel {s_id}", link)
        except Exception:
            return (s_id, name or f"Channel {s_id}", link)
    return None

async def check_force_sub(client, user_id, active_slots):
    tasks = [_check_single_slot(client, slot, user_id) for slot in active_slots]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res is not None]

# ----------------- /START COMMAND (INSTANT ULTRA-FAST) -----------------
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    
    asyncio.create_task(asyncio.to_thread(get_db, "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,), True))
    user_states.pop(user_id, None)
    asyncio.create_task(notify_owner_on_start(client, OWNER_ID, message.from_user))

    user = message.from_user
    first_name = user.first_name if user and user.first_name else "User"
    last_name = user.last_name if user and user.last_name else ""
    full_name = f"{first_name} {last_name}".strip()

    caption_task = get_caption_and_status_async(full_name)
    admin_task = asyncio.to_thread(is_admin, user_id, OWNER_ID)
    markup_task = asyncio.to_thread(get_colored_start_panel)
    media_file_task = asyncio.to_thread(get_setting, "media_file_id")
    media_type_task = asyncio.to_thread(get_setting, "media_type")
    voice_file_task = asyncio.to_thread(get_setting, "voice_file_id")

    status, offline_markup, caption_text = await caption_task
    is_user_admin, (markup, _), media_file, media_type, voice_file = await asyncio.gather(
        admin_task, markup_task, media_file_task, media_type_task, voice_file_task
    )

    if status == "offline" and not is_user_admin:
        return await message.reply_text("🔴 <b>Bot is currently Offline for maintenance.</b>", reply_markup=offline_markup, parse_mode=enums.ParseMode.HTML)

    caption_text = caption_text.replace("{name}", full_name)\
                               .replace("{first_name}", first_name)\
                               .replace("{mention}", user.mention if user else full_name)

    chat_id = message.chat.id

    try:
        if media_type == "photo" and media_file:
            await client.send_photo(chat_id, photo=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        elif media_type == "video" and media_file:
            await client.send_video(chat_id, video=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            await client.send_message(chat_id, text=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except Exception:
        await client.send_message(chat_id, text=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    if voice_file:
        try:
            await client.send_voice(chat_id, voice=voice_file)
        except Exception:
            pass

@app.on_callback_query(filters.regex("verify_sub"))
async def verify_cb(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    _, active_slots = await asyncio.to_thread(get_colored_start_panel)

    unjoined = await check_force_sub(client, user_id, active_slots)
    if unjoined:
        await callback.answer("❌ Aapne abhi tak saare channels join nahi kiye!", show_alert=True)
    else:
        await callback.answer("✅ Verified Successfully!", show_alert=False)
        
        raw_key = await asyncio.to_thread(get_setting, "get_key_url")
        raw_click = await asyncio.to_thread(get_setting, "click_url")
        final_key_url = clean_url(raw_click if (raw_click and str(raw_click).strip()) else raw_key)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        if final_key_url:
            key_msg = f"🎉 <b>SUCCESS! All channels verified.</b>\n\n🔑 <b>Your Key Link:</b> {final_key_url}"
        else:
            key_msg = f"🎉 <b>SUCCESS! All channels verified.</b>"
            
        await client.send_message(callback.message.chat.id, key_msg, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

async def send_start_panel_refresh(client, message, user_id):
    await start_cmd(client, message)

setup_admin_handlers(app, OWNER_ID, send_start_panel_refresh)

if __name__ == "__main__":
    print("🚀 Ultra-Fast Parallel Optimized Bot Started with Custom Emojis...")
    app.run()
