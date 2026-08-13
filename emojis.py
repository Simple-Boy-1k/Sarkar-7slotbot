# =========================================================
# TELEGRAM CUSTOM PREMIUM EMOJI IDs
# =========================================================

PREMIUM_EMOJI_IDS = {
    "FIRE": "6147565374289220368",
    "SWORDS": "6147565374289220368",
    "LOCK": "6147565374289220368",
    "TELEGRAM": "6147565374289220368",
    "KEY": "6147565374289220368",
    "PURPLE_STAR": "6147565374289220368",
    "GREEN_CHECK": "6147565374289220368"
}

def get_custom_emoji(emoji_key: str, fallback_symbol: str) -> str:
    """Returns HTML Tag for Custom Premium Emoji or Fallback Symbol."""
    emoji_id = PREMIUM_EMOJI_IDS.get(emoji_key, "")
    if emoji_id:
        return f'<emoji id="{emoji_id}">{fallback_symbol}</emoji>'
    return fallback_symbol

# --- READY-TO-USE ICONS FOR CAPTION TEXT (Animated) ---
ICON_FIRE = get_custom_emoji("FIRE", "🔥")
ICON_SWORDS = get_custom_emoji("SWORDS", "⚔️")
ICON_LOCK = get_custom_emoji("LOCK", "🚫")
ICON_TELEGRAM = get_custom_emoji("TELEGRAM", "📬")
ICON_KEY = get_custom_emoji("KEY", "🔑")

# --- BUTTON ICONS (High Quality Unicode for Buttons) ---
BTN_PURPLE_STAR = "💜"
BTN_GREEN_CHECK = "🟢"
