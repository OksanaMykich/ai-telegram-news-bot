import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models import Keyword, NewsItem
from app.news_parser.sites import parse_rss_feed
from app.utils import is_news_relevant
from celery_worker import celery_app
from app.news_parser.telegram import parse_telegram_channel


@celery_app.task
def test_task(name: str) -> str:
    return f"Hello, {name}! Celery is working."


async def parse_rss_source(source_name: str, feed_url: str) -> dict:
    try:
        parsed_items = parse_rss_feed(source_name=source_name, feed_url=feed_url)

        async with AsyncSessionLocal() as db:
            keywords_result = await db.execute(select(Keyword.word))
            keywords = list(keywords_result.scalars().all())

            filtered_count = 0
            added_count = 0

            for item in parsed_items:
                if not is_news_relevant(item, keywords):
                    continue

                filtered_count += 1
                existing_item = None

                if item["url"]:
                    result = await db.execute(
                        select(NewsItem).where(NewsItem.url == item["url"])
                    )
                    existing_item = result.scalar_one_or_none()

                if existing_item:
                    continue

                news_item = NewsItem(**item)
                db.add(news_item)
                added_count += 1

            await db.commit()

        return {
            "parsed_count": len(parsed_items),
            "filtered_count": filtered_count,
            "added_count": added_count,
        }
    finally:
        await engine.dispose()


@celery_app.task
def parse_rss_source_task(source_name: str, feed_url: str) -> dict:
    return asyncio.run(parse_rss_source(source_name, feed_url))

async def parse_telegram_source(channel_username: str, limit: int = 10) -> dict:
    try:
        parsed_items = await parse_telegram_channel(
            channel_username=channel_username,
            limit=limit,
        )

        async with AsyncSessionLocal() as db:
            keywords_result = await db.execute(select(Keyword.word))
            keywords = list(keywords_result.scalars().all())

            filtered_count = 0
            added_count = 0

            for item in parsed_items:
                if not is_news_relevant(item, keywords):
                    continue

                filtered_count += 1

                result = await db.execute(
                    select(NewsItem).where(
                        NewsItem.source == item["source"],
                        NewsItem.title == item["title"],
                    )
                )
                existing_item = result.scalar_one_or_none()

                if existing_item:
                    continue

                news_item = NewsItem(**item)
                db.add(news_item)
                added_count += 1

            await db.commit()

        return {
            "parsed_count": len(parsed_items),
            "filtered_count": filtered_count,
            "added_count": added_count,
        }
    finally:
        await engine.dispose()


@celery_app.task
def parse_telegram_source_task(channel_username: str, limit: int = 10) -> dict:
    return asyncio.run(parse_telegram_source(channel_username, limit))