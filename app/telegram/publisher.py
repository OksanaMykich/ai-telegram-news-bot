from telethon import TelegramClient

from app.config import settings


async def send_telegram_message(message: str) -> None:
    async with TelegramClient(
        settings.telegram_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    ) as client:
        await client.send_message(settings.telegram_target_channel, message)