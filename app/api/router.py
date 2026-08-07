from fastapi import APIRouter

from app.api.endpoints import generate, keywords, news, pipeline, posts, sources

api_router = APIRouter(prefix="/api")

api_router.include_router(sources.router)
api_router.include_router(keywords.router)
api_router.include_router(news.router)
api_router.include_router(posts.router)
api_router.include_router(generate.router)
api_router.include_router(pipeline.router)