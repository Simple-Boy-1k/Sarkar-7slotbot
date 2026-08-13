import asyncio
from pyrogram import Client, enums
from pyrogram.types import User

async def _send_alert(client: Client, owner_id: int, user: User):
    if not owner_id or owner_id == 0:
        return
    
    # Don't notify if owner starts their own bot
    if user.id == owner_id:
        return

    user_id = user.id
    first_name = user.first_name or "User"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "N/A"
    mention = user.mention(full_name)

    alert_text = (
        "🚀 <b>New User Started Bot!</b>\n\n"
        f"👤 <b>Name:</b> {mention}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🏷️ <b>Username:</b> {username}"
    )

    try:
        await client.send_message(
            chat_id=owner_id, 
            text=alert_text, 
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        print(f"⚠️ Start Notification Error: {e}")

def notify_owner_on_start(client: Client, owner_id: int, user: User):
    """ Non-blocking background call: User speed slow nahi hogi! """
    asyncio.create_task(_send_alert(client, owner_id, user))
