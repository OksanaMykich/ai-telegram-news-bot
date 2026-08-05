from fastapi import APIRouter, Depends, HTTPException
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_post_text
from app.api.schemas import GeneratePostRequest, PostRead
from app.database import get_db
from app.models import NewsItem, Post
from app.tasks import generate_post_for_news_task

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/", response_model=PostRead)
async def generate_post(
    request_data: GeneratePostRequest,
    db: AsyncSession = Depends(get_db),
):
    news_item = await db.get(NewsItem, request_data.news_id)

    if news_item is None:
        raise HTTPException(status_code=404, detail="News item not found")

    try:
        generated_text = await generate_post_text(
            title=news_item.title,
            summary=news_item.summary,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="OpenAI authentication failed. Check your API key.",
        )
    except RateLimitError:
        raise HTTPException(
            status_code=503,
            detail="OpenAI quota exceeded or rate limit reached.",
        )
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="OpenAI service is unavailable. Try again later.",
        )
    except APIError:
        raise HTTPException(
            status_code=502,
            detail="OpenAI API returned an error.",
        )

    post = Post(
        news_id=news_item.id,
        generated_text=generated_text,
        status="generated",
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post

@router.post("/task")
async def generate_post_task(request_data: GeneratePostRequest):
    task = generate_post_for_news_task.delay(request_data.news_id)

    return {
        "task_id": task.id,
        "status": "queued",
    }