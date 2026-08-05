from datetime import UTC, datetime

from telethon import TelegramClient

from app.config import settings


async def parse_telegram_channel(channel_username: str, limit: int = 10) -> list[dict]:
    news_items = []

    async with TelegramClient(
        settings.telegram_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    ) as client:
        async for message in client.iter_messages(channel_username, limit=limit):
            if not message.text:
                continue

            news_items.append(
                {
                    "title": message.text[:120],
                    "url": None,
                    "summary": message.text[:500],
                    "source": channel_username,
                    "published_at": (message.date or datetime.now(UTC)).replace(tzinfo=None),
                    "raw_text": message.text,
                }
            )

    return news_items