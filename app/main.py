from fastapi import FastAPI

from app.api.endpoints import router
from app.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}