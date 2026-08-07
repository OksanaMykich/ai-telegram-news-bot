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
from app.error_logger import save_error_log


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
                    error_message = f"Unsupported source type: {source['type']}"

                    await save_error_log(
                        message=error_message,
                        source=source["name"],
                        task_name="parse_enabled_sources_task",
                    )

                    task_result = {
                        "status": "skipped",
                        "error": error_message,
                    }

                results.append(
                    {
                        "source": source["name"],
                        "type": source["type"],
                        "result": task_result,
                    }
                )

            except Exception as exc:
                logger.exception(
                    "Failed to parse source: name=%s type=%s",
                    source["name"],
                    source["type"],
                )
                await save_error_log(
                    message=str(exc),
                    source=source["name"],
                    task_name="parse_enabled_sources_task",
                )
                results.append(
                    {
                        "source": source["name"],
                        "type": source["type"],
                        "status": "failed",
                        "error": str(exc),
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

async def generate_posts_for_unprocessed_news(limit: int = 5):
    logger.info("Starting bulk AI generation task: limit=%s", limit)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(NewsItem.id)
            .outerjoin(Post, Post.news_id == NewsItem.id)
            .where(Post.id.is_(None))
            .order_by(NewsItem.published_at.desc())
            .limit(limit)
        )

        news_ids = result.scalars().all()

    generated_count = 0
    failed_count = 0
    skipped_count = 0
    results = []

    for news_id in news_ids:
        task_result = await generate_post_for_news(news_id)
        results.append(
            {
                "news_id": news_id,
                "result": task_result,
            }
        )

        status = task_result.get("status")

        if status == "generated":
            generated_count += 1
        elif status == "failed":
            failed_count += 1
        else:
            skipped_count += 1

    logger.info(
        "Finished bulk AI generation task: found=%s generated=%s failed=%s skipped=%s",
        len(news_ids),
        generated_count,
        failed_count,
        skipped_count,
    )

    return {
        "status": "completed",
        "found_count": len(news_ids),
        "generated_count": generated_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }


@celery_app.task
def generate_posts_for_unprocessed_news_task(limit: int = 5):
    return asyncio.run(generate_posts_for_unprocessed_news(limit))

async def publish_generated_posts(limit: int = 5):
    logger.info("Starting bulk Telegram publishing task: limit=%s", limit)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post.id)
            .where(Post.status == "generated")
            .where(Post.published_at.is_(None))
            .order_by(Post.id.asc())
            .limit(limit)
        )

        post_ids = result.scalars().all()

    published_count = 0
    failed_count = 0
    skipped_count = 0
    results = []

    for post_id in post_ids:
        task_result = await publish_post_to_telegram(post_id)
        results.append(
            {
                "post_id": post_id,
                "result": task_result,
            }
        )

        status = task_result.get("status")

        if status == "published":
            published_count += 1
        elif status == "failed":
            failed_count += 1
        else:
            skipped_count += 1

    logger.info(
        "Finished bulk Telegram publishing task: found=%s published=%s failed=%s skipped=%s",
        len(post_ids),
        published_count,
        failed_count,
        skipped_count,
    )

    return {
        "status": "completed",
        "found_count": len(post_ids),
        "published_count": published_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "results": results,
    }


@celery_app.task
def publish_generated_posts_task(limit: int = 5):
    return asyncio.run(publish_generated_posts(limit))

async def run_news_pipeline(generation_limit: int = 5, publishing_limit: int = 5):
    logger.info(
        "Starting news pipeline: generation_limit=%s publishing_limit=%s",
        generation_limit,
        publishing_limit,
    )

    parsing_result = await parse_enabled_sources()
    generation_result = await generate_posts_for_unprocessed_news(generation_limit)
    publishing_result = await publish_generated_posts(publishing_limit)

    logger.info(
        "Finished news pipeline: parsed_sources=%s generated=%s published=%s",
        parsing_result.get("sources_count"),
        generation_result.get("generated_count"),
        publishing_result.get("published_count"),
    )

    return {
        "status": "completed",
        "parsing": parsing_result,
        "generation": generation_result,
        "publishing": publishing_result,
    }


@celery_app.task
def run_news_pipeline_task(generation_limit: int = 5, publishing_limit: int = 5):
    return asyncio.run(run_news_pipeline(generation_limit, publishing_limit))