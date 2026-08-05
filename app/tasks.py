import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Keyword, NewsItem
from app.news_parser.sites import parse_rss_feed
from app.utils import is_news_relevant
from celery_worker import celery_app


@celery_app.task
def test_task(name: str) -> str:
    return f"Hello, {name}! Celery is working."


async def parse_rss_source(source_name: str, feed_url: str) -> dict:
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


@celery_app.task
def parse_rss_source_task(source_name: str, feed_url: str) -> dict:
    return asyncio.run(parse_rss_source(source_name, feed_url))