from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PostCreate, PostRead
from app.database import get_db
from app.models import Post
from app.telegram.publisher import send_telegram_message

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostRead)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
):
    post = Post(**post_data.model_dump())

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post


@router.get("/", response_model=list[PostRead])
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post))
    return result.scalars().all()

@router.post("/{post_id}/publish", response_model=PostRead)
async def publish_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == "published":
        raise HTTPException(status_code=400, detail="Post already published")

    await send_telegram_message(post.generated_text)

    post.status = "published"
    post.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(post)

    return post