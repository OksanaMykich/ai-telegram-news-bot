from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SourceCreate, SourceRead
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


