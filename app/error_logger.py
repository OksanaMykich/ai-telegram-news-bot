import logging

from app.database import AsyncSessionLocal
from app.models import ErrorLog

logger = logging.getLogger(__name__)


async def save_error_log(
    message: str,
    source: str | None = None,
    task_name: str | None = None,
):
    try:
        async with AsyncSessionLocal() as session:
            error_log = ErrorLog(
                message=message,
                source=source,
                task_name=task_name,
            )

            session.add(error_log)
            await session.commit()
    except Exception:
        logger.exception("Failed to save error log")