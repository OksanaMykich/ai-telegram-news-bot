from celery import Celery

from app.config import settings


celery_app = Celery(
    "aibot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app"])

celery_app.conf.beat_schedule = {
    "run-news-pipeline-every-30-minutes": {
        "task": "app.tasks.run_news_pipeline_task",
        "schedule": 30 * 60,
        "args": (5, 5),
    },
}

celery_app.conf.timezone = "Europe/Kyiv"

