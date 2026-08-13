# =========================================================
# PASTE YOUR TELEGRAM PREMIUM EMOJI IDs HERE
# (Agar ID nahi hai toh khali "" chhod dein, normal emoji chalega)
# =========================================================

ID_WELCOME_HEAD     = "6077883305187876926"  # 🔴 Mark 1: Welcome se pehle (e.g. 🔥)
ID_KEY_HEAD_LEFT1   = "6269194596094317437"  # 🔴 Mark 2: How To Get Key ke left me pehla (e.g. 🟢)
ID_KEY_HEAD_LEFT2   = "6079974593483775722"  # 🔴 Mark 2: How To Get Key ke left me doosra (e.g. ⚡)
ID_KEY_HEAD_RIGHT1  = "6237552274944564087"  # 🔴 Mark 3: How To Get Key ke right me pehla (e.g. 💨)
ID_KEY_HEAD_RIGHT2  = "6244425785986257276"  # 🔴 Mark 3: How To Get Key ke right me doosra (e.g. 📈)
ID_GET_KEY_LEFT     = "6010103971023166824"  # 🔴 Mark 4: GET KEY ke left me (e.g. 🤫)
ID_GET_KEY_RIGHT    = "6271271702408204490"  # 🔴 Mark 5: GET KEY ke right me (e.g. 🔔)

# Helper Function
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
