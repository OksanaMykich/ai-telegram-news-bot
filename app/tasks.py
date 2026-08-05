from celery_worker import celery_app


@celery_app.task
def test_task(name: str) -> str:
    return f"Hello, {name}! Celery is working."