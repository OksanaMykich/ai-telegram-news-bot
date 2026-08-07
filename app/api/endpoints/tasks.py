from celery.result import AsyncResult
from fastapi import APIRouter

from celery_worker import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.failed():
        response["error"] = str(task_result.result)
    elif task_result.ready():
        response["result"] = task_result.result

    return response