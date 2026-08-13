import os
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

async def send_start_panel(client, message, user_id):
    if get_setting("bot_status") == "offline" and not is_admin(user_id, OWNER_ID):
        offline_chan = get_setting("offline_channel") or "https://t.me"
        return await message.reply_text(
            "🔴 <b>Bot is currently Offline for maintenance.</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Official Channel", url=offline_chan)]]),
            parse_mode=enums.ParseMode.HTML
        )

    user = message.from_user
    first_name = user.first_name if user and user.first_name else "User"
    last_name = user.last_name if user and user.last_name else ""
    full_name = f"{first_name} {last_name}".strip()
    mention = user.mention if user else full_name

    get_key_link = get_setting("get_key_url")

    header = f"{emojis.EMOJI_WELCOME_HEAD} <b>Welcome {full_name}</b>\n\n"
    
    # How To Get Key section - ONLY IF LINK IS SET
    if get_key_link and get_key_link.strip():
        footer = (
            f"\n\n{emojis.EMOJI_KEY_HEAD_LEFT1} {emojis.EMOJI_KEY_HEAD_LEFT2} <b>How To Get Key</b> {emojis.EMOJI_KEY_HEAD_RIGHT1} {emojis.EMOJI_KEY_HEAD_RIGHT2}\n"
            f"{emojis.EMOJI_GET_KEY_LEFT} <a href='{get_key_link.strip()}'><b>GET KEY</b></a> {emojis.EMOJI_GET_KEY_RIGHT}"
        )
    else:
        footer = ""

    custom_text = get_setting("promo_text")

    if custom_text:
        formatted_text = custom_text.replace("{name}", full_name)\
                                    .replace("{first_name}", first_name)\
                                    .replace("{mention}", mention)
        
        if get_key_link and get_key_link.strip():
            formatted_text = formatted_text.replace("{key_link}", get_key_link.strip())

        if "GET KEY" in custom_text or "How To Get Key" in custom_text:
            caption_text = formatted_text
        else:
            caption_text = f"{header}{formatted_text}{footer}"
    else:
        middle = "🚫 <b>Join All Channels To Unlock</b> 📬"
        caption_text = f"{header}{middle}{footer}"

    media_file = get_setting("media_file_id")
    media_type = get_setting("media_type")
    voice_file = get_setting("voice_file_id")

    inline_buttons = []
    all_slots = get_db("SELECT id, name, link FROM slots ORDER BY id ASC")
    active_slots = [s for s in all_slots if s[2] and s[2].strip()]

    # Channels 2-column Grid
    for i in range(0, len(active_slots), 2):
        row = []
        s1 = active_slots[i]
        row.append(InlineKeyboardButton(text=f"💜 {s1[1] or f'Channel {s1[0]} '}", url=s1[2]))
        if i + 1 < len(active_slots):
            s2 = active_slots[i+1]
            row.append(InlineKeyboardButton(text=f"💜 {s2[1] or f'Channel {s2[0]} '}", url=s2[2]))
        inline_buttons.append(row)

    # Click Here Button (if set)
    click_name = get_setting("click_name")
    click_url = get_setting("click_url")
    if click_name and click_url and click_url.strip():
        inline_buttons.append([InlineKeyboardButton(text=f"✨ {click_name}", url=click_url.strip())])

    # Check Joined Button
    verify_url = get_setting("verify_url")
    if verify_url and verify_url.strip():
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", url=verify_url.strip())])
    else:
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", callback_data="verify_sub")])

    markup = InlineKeyboardMarkup(inline_buttons)

    if media_type == "photo" and media_file:
        await client.send_photo(message.chat.id, photo=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    elif media_type == "video" and media_file:
        await client.send_video(message.chat.id, video=media_file, caption=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        await client.send_message(message.chat.id, text=caption_text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    if voice_file:
        await client.send_voice(message.chat.id, voice=voice_file)

@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    get_db("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,), commit=True)
    user_states.pop(user_id, None)
    await send_start_panel(client, message, user_id)

@app.on_callback_query(filters.regex("verify_sub"))
async def verify_cb(client, callback: CallbackQuery):
    if get_setting("bot_status") == "offline" and not is_admin(callback.from_user.id, OWNER_ID):
        return await callback.answer("🔴 Bot is currently offline for maintenance!", show_alert=True)

    user_id = callback.from_user.id
    unjoined = await check_force_sub(client, user_id)
    if unjoined:
        await callback.answer("❌ Aapne abhi tak saare channels join nahi kiye!", show_alert=True)
    else:
        await callback.answer("✅ Verified Successfully!", show_alert=False)
        get_key_url = get_setting("get_key_url")
        await callback.message.delete()
        if get_key_url and get_key_url.strip():
            key_msg = f"🎉 <b>SUCCESS! All channels verified.</b>\n\n🔑 <b>Your Key Link:</b> {get_key_url.strip()}"
        else:
            key_msg = "🎉 <b>SUCCESS! All channels verified.</b>"
        await client.send_message(callback.message.chat.id, key_msg, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

setup_admin_handlers(app, OWNER_ID, send_start_panel)

if __name__ == "__main__":
    app.run()
