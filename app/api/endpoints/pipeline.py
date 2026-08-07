from fastapi import APIRouter

from app.tasks import run_news_pipeline_task

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run")
async def run_pipeline(
    generation_limit: int = 5,
    publishing_limit: int = 5,
    language: str | None = None,
):
    task = run_news_pipeline_task.delay(
        generation_limit,
        publishing_limit,
        language,
    )

    return {
        "task_id": task.id,
        "status": "queued",
        "generation_limit": generation_limit,
        "publishing_limit": publishing_limit,
        "language": language,
    }