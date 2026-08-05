from app.ai.openai_client import client
from app.config import settings


SYSTEM_PROMPT = (
    "You are an assistant that writes short, engaging Telegram news posts. "
    "Write in Ukrainian. Add relevant emoji and a short call to action."
)


async def generate_post_text(title: str, summary: str) -> str:
    user_prompt = (
        f"Title: {title}\n"
        f"Summary: {summary}\n\n"
        "Create a short Telegram post based on this news."
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content