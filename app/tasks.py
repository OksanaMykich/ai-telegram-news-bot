import asyncio
import logging
from datetime import UTC, datetime

from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError
from sqlalchemy import select

from app.ai.generator import generate_post_text
from app.database import AsyncSessionLocal, engine
from app.models import Keyword, NewsItem, Post, Source
from app.news_parser.sites import parse_rss_feed
from app.news_parser.telegram import parse_telegram_channel
from app.telegram.publisher import send_telegram_message
from app.utils import is_news_relevant
from celery_worker import celery_app


logger = logging.getLogger(__name__)


@celery_app.task
def test_task(name: str) -> str:
    return f"Hello, {name}! Celery is working."


async def parse_rss_source(source_name: str, feed_url: str) -> dict:
    try:
        logger.info("Starting RSS parsing task: source=%s", source_name)

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

        logger.info(
            "Finished RSS parsing task: parsed=%s filtered=%s added=%s",
            len(parsed_items),
            filtered_count,
            added_count,
        )

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
        logger.info(
            "Starting Telegram parsing task: channel=%s limit=%s",
            channel_username,
            limit,
        )

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

        logger.info(
            "Finished Telegram parsing task: parsed=%s filtered=%s added=%s",
            len(parsed_items),
            filtered_count,
            added_count,
        )

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


async def parse_enabled_sources() -> dict:
    try:
        logger.info("Starting enabled sources parsing task")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Source).where(Source.enabled.is_(True)))
            sources = result.scalars().all()

            source_configs = [
                {
                    "type": source.type,
                    "name": source.name,
                    "url": source.url,
                }
                for source in sources
            ]

        results = []

        for source in source_configs:
            source_type = source["type"].lower()

            try:
                if source_type == "site":
                    task_result = await parse_rss_source(
                        source_name=source["name"],
                        feed_url=source["url"],
                    )
                elif source_type in {"tg", "telegram"}:
                    task_result = await parse_telegram_source(
                        channel_username=source["url"],
                        limit=10,
                    )
                else:
                    task_result = {
                        "status": "skipped",
                        "error": f"Unsupported source type: {source['type']}",
                    }

                results.append(
                    {
                        "source": source["name"],
                        "type": source["type"],
                        "result": task_result,
                    }
                )
            except Exception as exc:
                logger.exception("Failed to parse source: %s", source["name"])
                results.append(
                    {
                        "source": source["name"],
                        "type": source["type"],
                        "result": {
                            "status": "failed",
                            "error": str(exc),
                        },
                    }
                )

        logger.info("Finished enabled sources parsing task: sources=%s", len(results))

        return {
            "status": "completed",
            "sources_count": len(results),
            "results": results,
        }
    finally:
        await engine.dispose()


@celery_app.task
def parse_enabled_sources_task() -> dict:
    return asyncio.run(parse_enabled_sources())


async def generate_post_for_news(news_id: int) -> dict:
    try:
        logger.info("Starting AI generation task: news_id=%s", news_id)

        async with AsyncSessionLocal() as db:
            news_item = await db.get(NewsItem, news_id)

            if news_item is None:
                logger.warning("News item not found for AI generation: news_id=%s", news_id)
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
                logger.warning("OpenAI authentication failed: news_id=%s", news_id)
                return {
                    "status": "failed",
                    "error": "OpenAI authentication failed",
                }
            except RateLimitError:
                logger.warning(
                    "OpenAI quota exceeded while generating post: news_id=%s",
                    news_id,
                )
                return {
                    "status": "failed",
                    "error": "OpenAI quota exceeded or rate limit reached",
                }
            except APIConnectionError:
                logger.warning("OpenAI service unavailable: news_id=%s", news_id)
                return {
                    "status": "failed",
                    "error": "OpenAI service is unavailable",
                }
            except APIError:
                logger.warning("OpenAI API returned an error: news_id=%s", news_id)
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

            logger.info(
                "Finished AI generation task: news_id=%s post_id=%s",
                news_item.id,
                post.id,
            )

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


async def publish_post_to_telegram(post_id: int) -> dict:
    try:
        logger.info("Starting Telegram publishing task: post_id=%s", post_id)

        async with AsyncSessionLocal() as db:
            post = await db.get(Post, post_id)

            if post is None:
                logger.warning("Post not found for Telegram publishing: post_id=%s", post_id)
                return {
                    "status": "failed",
                    "error": "Post not found",
                }

            if post.status == "published":
                logger.info("Post already published, skipping: post_id=%s", post.id)
                return {
                    "status": "skipped",
                    "error": "Post already published",
                    "post_id": post.id,
                }

            await send_telegram_message(post.generated_text)

            post.status = "published"
            post.published_at = datetime.now(UTC).replace(tzinfo=None)

            await db.commit()
            await db.refresh(post)

            logger.info("Finished Telegram publishing task: post_id=%s", post.id)

            return {
                "status": "published",
                "post_id": post.id,
            }
    finally:
        await engine.dispose()


@celery_app.task
def publish_post_to_telegram_task(post_id: int) -> dict:
    return asyncio.run(publish_post_to_telegram(post_id))