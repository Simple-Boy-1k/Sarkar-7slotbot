import asyncio
from pyrogram import Client
from pyrogram.types import User

async def notify_owner_on_start(client: Client, owner_id: int, user: User):
    """ Sends notification to owner safely in background. """
    if not owner_id or not user or user.id == owner_id:
        return
    
    try:
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        user_text = (
            f"👤 <b>New User Started Bot!</b>\n\n"
            f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
            f"📛 <b>Name:</b> {user.mention or user_name}"
        )
        await client.send_message(owner_id, user_text)
    except Exception:
        pass
