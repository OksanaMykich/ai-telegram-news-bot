from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import KeywordCreate, KeywordRead, KeywordUpdate
from app.database import get_db
from app.models import Keyword

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.post("/", response_model=KeywordRead)
async def create_keyword(keyword_data: KeywordCreate, db: AsyncSession = Depends(get_db)):
    keyword = Keyword(**keyword_data.model_dump())

    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)

    return keyword


@router.get("/", response_model=list[KeywordRead])
async def get_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword))
    return result.scalars().all()


@router.put("/{keyword_id}", response_model=KeywordRead)
async def update_keyword(
    keyword_id: int,
    keyword_data: KeywordUpdate,
    db: AsyncSession = Depends(get_db),
):
    keyword = await db.get(Keyword, keyword_id)

    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    for field, value in keyword_data.model_dump().items():
        setattr(keyword, field, value)

    await db.commit()
    await db.refresh(keyword)

    return keyword


@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    keyword = await db.get(Keyword, keyword_id)

    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await db.delete(keyword)
    await db.commit()

    return {"message": "Keyword deleted"}