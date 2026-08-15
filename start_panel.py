from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_db, get_setting

def clean_url(url):
    """ Fast URL Fixer with Strict Validation """
    if not url:
        return None
    url = str(url).strip().replace(" ", "")
    if not url or url.lower() in ["none", "null", "remove", "deleted"]:
        return None
    
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        url = f"https://{url}"
        
    # Validation: Agar URL me proper domain/dot nahi hai, toh use invalid maan kar hata do
    if "." not in url and not url.startswith("tg://"):
        return None
        
    return url



def get_colored_start_panel():
    """ Super Fast & Vibrant Solid Blue / Green Buttons """
    all_slots = get_db("SELECT id, chat_id, name, link FROM slots ORDER BY id ASC") or []
    
    active_slots = []
    for s in all_slots:
        if isinstance(s, (list, tuple)) and len(s) >= 4 and s[3]:
            link = clean_url(s[3])
            if link:
                active_slots.append((s[0], s[1], s[2], link))

    inline_buttons = []
    i = 0
    total = len(active_slots)
    
    # 2-Buttons Row System + Single Bottom Button
    while i < total:
        if i == total - 1 and total % 2 != 0:
            s = active_slots[i]
            s_name = s[2] if (s[2] and str(s[2]).strip()) else f"Channel {s[0]}"
            inline_buttons.append([
                InlineKeyboardButton(text=f"⭐ {s_name}", url=s[3])
            ])
            i += 1
        else:
            row = []
            s1 = active_slots[i]
            s1_name = s1[2] if (s1[2] and str(s1[2]).strip()) else f"Channel {s1[0]}"
            row.append(InlineKeyboardButton(text=f"🌟 {s1_name}", url=s1[3]))

            
            if i + 1 < total:
                s2 = active_slots[i+1]
                s2_name = s2[2] if (s2[2] and str(s2[2]).strip()) else f"Channel {s2[0]}"
                row.append(InlineKeyboardButton(text=f"⭐ {s2_name}", url=s2[3]))
                i += 2
            else:
                i += 1
                
            inline_buttons.append(row)

    # 🟩 Check Joined Button
    verify_url = clean_url(get_setting("verify_url"))
    if verify_url:
        inline_buttons.append([
            InlineKeyboardButton(text="🟢 Check Joined", url=verify_url)
        ])
    else:
        inline_buttons.append([
            InlineKeyboardButton(text="🟢 Check Joined", callback_data="verify_sub")
        ])

    markup = InlineKeyboardMarkup(inline_buttons) if inline_buttons else None
    return markup, active_slots
