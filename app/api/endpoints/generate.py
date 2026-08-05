from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_post_text
from app.api.schemas import GeneratePostRequest, PostRead
from app.database import get_db
from app.models import NewsItem, Post

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/", response_model=PostRead)
async def generate_post(
    request_data: GeneratePostRequest,
    db: AsyncSession = Depends(get_db),
):
    news_item = await db.get(NewsItem, request_data.news_id)

    if news_item is None:
        raise HTTPException(status_code=404, detail="News item not found")

    generated_text = generate_post_text(
        title=news_item.title,
        summary=news_item.summary,
    )

    post = Post(
        news_id=news_item.id,
        generated_text=generated_text,
        status="generated",
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post