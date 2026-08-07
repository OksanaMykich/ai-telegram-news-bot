from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ErrorLogRead
from app.database import get_db
from app.models import ErrorLog

router = APIRouter(prefix="/error-logs", tags=["error logs"])


@router.get("/", response_model=list[ErrorLogRead])
async def get_error_logs(
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(ErrorLog)
        .order_by(desc(ErrorLog.created_at))
        .limit(limit)
    )

    return result.scalars().all()