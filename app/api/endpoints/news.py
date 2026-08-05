from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import NewsItemCreate, NewsItemRead, RSSParseRequest
from app.database import get_db
from app.models import NewsItem
from app.news_parser.sites import parse_rss_feed

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/", response_model=NewsItemRead)
async def create_news_item(
    news_data: NewsItemCreate,
    db: AsyncSession = Depends(get_db),
):
    news_item = NewsItem(**news_data.model_dump())

    db.add(news_item)
    await db.commit()
    await db.refresh(news_item)

    return news_item


@router.get("/", response_model=list[NewsItemRead])
async def get_news_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsItem))
    return result.scalars().all()

@router.post("/parse-rss")
async def parse_rss_news(
    request_data: RSSParseRequest,
    db: AsyncSession = Depends(get_db),
):
    parsed_items = parse_rss_feed(
        source_name=request_data.source_name,
        feed_url=request_data.feed_url,
    )

    added_count = 0

    for item in parsed_items:
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
        "added_count": added_count,
    }