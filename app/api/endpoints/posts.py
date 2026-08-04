from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PostCreate, PostRead
from app.database import get_db
from app.models import Post

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