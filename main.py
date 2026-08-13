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
    slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC") or []
    unjoined = []
    for slot in slots:
        if not isinstance(slot, (list, tuple)) or len(slot) < 4:
            continue
        s_id, chat_id, name, link = slot[0], slot[1], slot[2], slot[3]
        if link and str(link).strip():
            if chat_id and str(chat_id).strip():
                try:
                    member = await client.get_chat_member(str(chat_id).strip(), user_id)
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

    raw_key = get_setting("get_key_url")
    raw_click = get_setting("click_url")
    
    get_key_link = raw_click if (raw_click and str(raw_click).strip()) else raw_key
    has_key_link = bool(get_key_link and str(get_key_link).strip())

    header = f"{emojis.EMOJI_WELCOME_HEAD} <b>Welcome {full_name} 🌹</b>\n\n"
    
    if has_key_link:
        footer = (
            f"\n\n{emojis.EMOJI_KEY_HEAD_LEFT1} {emojis.EMOJI_KEY_HEAD_LEFT2} <b>𝐇𝐨𝐰 𝐓𝐨 𝐆𝐞𝐭 𝐊𝐞𝐲</b> {emojis.EMOJI_KEY_HEAD_RIGHT1} {emojis.EMOJI_KEY_HEAD_RIGHT2}\n"
            f"{emojis.EMOJI_GET_KEY_LEFT} <a href='{str(get_key_link).strip()}'><b>𝐆𝐞𝐭 𝐊𝐞𝐲 </b></a> {emojis.EMOJI_GET_KEY_RIGHT}"
        )
    else:
        footer = ""

    custom_text = get_setting("promo_text")

    if custom_text:
        formatted_text = str(custom_text).replace("{name}", full_name)\
                                          .replace("{first_name}", first_name)\
                                          .replace("{mention}", mention)
        
        if has_key_link:
            formatted_text = formatted_text.replace("{key_link}", str(get_key_link).strip())

        if "   𝐆𝐞𝐭 𝐊𝐞𝐲" in custom_text or "𝐇𝐨𝐰 𝐓𝐨 𝐆𝐞𝐭 𝐊𝐞𝐲" in custom_text:
            caption_text = formatted_text
        else:
            caption_text = f"{header}{formatted_text}{footer}"
    else:
        middle = "🚫 <b>𝐉𝐨𝐢𝐧 𝐀𝐥𝐥 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐓𝐨 𝐔𝐧𝐥𝐨𝐜𝐤 </b> 📬"
        caption_text = f"{header}{middle}{footer}"

    media_file = get_setting("media_file_id")
    media_type = get_setting("media_type")
    voice_file = get_setting("voice_file_id")

    inline_buttons = []
    all_slots = get_db("SELECT id, name, link FROM slots ORDER BY id ASC") or []
    
    active_slots = []
    for s in all_slots:
        if isinstance(s, (list, tuple)) and len(s) >= 3 and s[2] and str(s[2]).strip():
            active_slots.append(s)

    for i in range(0, len(active_slots), 2):
        row = []
        s1 = active_slots[i]
        s1_name = s1[1] if len(s1) > 1 and s1[1] else f"Channel {s1[0]}"
        row.append(InlineKeyboardButton(text=f"💜 {s1_name}", url=str(s1[2])))
        
        if i + 1 < len(active_slots):
            s2 = active_slots[i+1]
            s2_name = s2[1] if len(s2) > 1 and s2[1] else f"Channel {s2[0]}"
            row.append(InlineKeyboardButton(text=f"💜 {s2_name}", url=str(s2[2])))
            
        inline_buttons.append(row)

    # Check Joined Button
    verify_url = get_setting("verify_url")
    if verify_url and str(verify_url).strip():
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", url=str(verify_url).strip())])
    else:
        inline_buttons.append([InlineKeyboardButton(text="🟢 Check Joined", callback_data="verify_sub")])

    markup = InlineKeyboardMarkup(inline_buttons) if inline_buttons else None

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
        
        raw_key = get_setting("get_key_url")
        raw_click = get_setting("click_url")
        final_key_url = raw_click if (raw_click and str(raw_click).strip()) else raw_key
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        if final_key_url and str(final_key_url).strip():
            key_msg = f"🎉 <b>SUCCESS! All channels verified.</b>\n\n🔑 <b>Your Key Link:</b> {str(final_key_url).strip()}"
        else:
            key_msg = "🎉 <b>SUCCESS! All channels verified.</b>"
            
        await client.send_message(callback.message.chat.id, key_msg, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

setup_admin_handlers(app, OWNER_ID, send_start_panel)

if __name__ == "__main__":
    print("🚀 Bot starting...")
    app.run()
