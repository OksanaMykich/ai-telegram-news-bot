import asyncio

from sqlalchemy import select
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from app.database import AsyncSessionLocal, engine
from app.models import Keyword, NewsItem, Post
from app.news_parser.sites import parse_rss_feed
from app.utils import is_news_relevant
from celery_worker import celery_app
from app.news_parser.telegram import parse_telegram_channel
from app.ai.generator import generate_post_text


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

async def generate_post_for_news(news_id: int) -> dict:
    try:
        async with AsyncSessionLocal() as db:
            news_item = await db.get(NewsItem, news_id)

            if news_item is None:
                return {
                    "status": "failed",
                    "error": "News item not found",
                }

            try:
                generated_text = await generate_post_text(
                    title=news_item.title,
                    summary=news_item.summary,
                )
            except AuthenticationError:
                return {
                    "status": "failed",
                    "error": "OpenAI authentication failed",
                }
            except RateLimitError:
                return {
                    "status": "failed",
                    "error": "OpenAI quota exceeded or rate limit reached",
                }
            except APIConnectionError:
                return {
                    "status": "failed",
                    "error": "OpenAI service is unavailable",
                }
            except APIError:
                return {
                    "status": "failed",
                    "error": "OpenAI API returned an error",
                }

            post = Post(
                news_id=news_item.id,
                generated_text=generated_text,
                status="generated",
            )

            db.add(post)
            await db.commit()
            await db.refresh(post)

            return {
                "status": "generated",
                "post_id": post.id,
                "news_id": news_item.id,
            }
    finally:
        await engine.dispose()


@celery_app.task
def generate_post_for_news_task(news_id: int) -> dict:
    return asyncio.run(generate_post_for_news(news_id))