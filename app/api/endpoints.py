from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    KeywordCreate,
    KeywordRead,
    KeywordUpdate,
    SourceCreate,
    SourceRead,
    SourceUpdate,
)
from app.database import get_db
from app.models import Keyword, Source

router = APIRouter(prefix="/api")


@router.post("/sources/", response_model=SourceRead)
async def create_source(source_data: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = Source(**source_data.model_dump())

    db.add(source)
    await db.commit()
    await db.refresh(source)

    return source

@router.get("/sources/", response_model=list[SourceRead])
async def get_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source))
    return result.scalars().all()

@router.put("/sources/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(Source, source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    for field, value in source_data.model_dump().items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    return source


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()

    return {"message": "Source deleted"}


@router.post("/keywords/", response_model=KeywordRead)
async def create_keyword(keyword_data: KeywordCreate, db: AsyncSession = Depends(get_db)):
    keyword = Keyword(**keyword_data.model_dump())

    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)

    return keyword


@router.get("/keywords/", response_model=list[KeywordRead])
async def get_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword))
    return result.scalars().all()


@router.put("/keywords/{keyword_id}", response_model=KeywordRead)
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


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    keyword = await db.get(Keyword, keyword_id)

    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await db.delete(keyword)
    await db.commit()

    return {"message": "Keyword deleted"}

