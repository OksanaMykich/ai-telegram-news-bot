from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import NewsItemCreate, NewsItemRead
from app.database import get_db
from app.models import NewsItem

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