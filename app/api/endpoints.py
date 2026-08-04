from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SourceCreate, SourceRead, SourceUpdate
from app.database import get_db
from app.models import Source

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

