from celery import Celery

from app.config import settings


celery_app = Celery(
    "aibot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app"])

celery_app.conf.beat_schedule = {
    "parse-bbc-rss-every-30-minutes": {
        "task": "app.tasks.parse_rss_source_task",
        "schedule": 30 * 60,
        "args": ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    },
}

celery_app.conf.timezone = "Europe/Kyiv"