# AI Telegram News Bot

A FastAPI service for collecting news from websites and Telegram channels, filtering relevant items, generating Telegram posts with AI, and publishing them to a Telegram channel.

## Current Features

- FastAPI application with Swagger documentation
- PostgreSQL database with Alembic migrations
- Source CRUD API
- Keyword CRUD API
- News item API
- Post history API
- RSS news parser
- Telegram channel parser
- Keyword-based news filtering
- Manual AI post generation with OpenAI API
- OpenAI error handling
- Telegram post publishing with Telethon
- Redis + Celery worker
- Celery Beat scheduled RSS parsing
- Celery tasks for RSS and Telegram parsing
- Basic logging for RSS parsing

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn
- Redis
- Celery
- Celery Beat
- OpenAI API
- Telethon
- feedparser
- Docker

## Project Structure

```text
app/
├── ai/
│   ├── __init__.py
│   ├── generator.py
│   └── openai_client.py
├── api/
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── generate.py
│   │   ├── keywords.py
│   │   ├── news.py
│   │   ├── posts.py
│   │   └── sources.py
│   ├── router.py
│   └── schemas.py
├── news_parser/
│   ├── __init__.py
│   ├── sites.py
│   └── telegram.py
├── telegram/
│   ├── __init__.py
│   └── publisher.py
├── config.py
├── database.py
├── logging_config.py
├── main.py
├── models.py
├── tasks.py
└── utils.py
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
APP_NAME=AI Telegram News Bot
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aibot
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
TELEGRAM_API_ID=your_telegram_api_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
TELEGRAM_SESSION_NAME=aibot_session
TELEGRAM_TARGET_CHANNEL=@your_channel_username
```

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Database

Create a PostgreSQL database named:

```text
aibot
```

Run migrations:

```powershell
alembic upgrade head
```

## Redis

Start Redis with Docker:

```powershell
docker start aibot-redis
```

If the Redis container does not exist yet, create it:

```powershell
docker run --name aibot-redis -p 6379:6379 -d redis:7
```

## Running the App

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

Open Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Background Services

Start Celery worker:

```powershell
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

Start Celery Beat:

```powershell
celery -A celery_worker.celery_app beat --loglevel=info
```

## API Endpoints

```text
GET    /health

POST   /api/sources/
GET    /api/sources/
PUT    /api/sources/{source_id}
DELETE /api/sources/{source_id}

POST   /api/keywords/
GET    /api/keywords/
PUT    /api/keywords/{keyword_id}
DELETE /api/keywords/{keyword_id}

POST   /api/news/
GET    /api/news/
POST   /api/news/parse-rss
POST   /api/news/parse-rss-task
POST   /api/news/parse-telegram-task

POST   /api/generate/

POST   /api/posts/
GET    /api/posts/
POST   /api/posts/{post_id}/publish
```

## Example RSS Parsing Request

```json
{
  "source_name": "BBC News",
  "feed_url": "https://feeds.bbci.co.uk/news/rss.xml"
}
```

## Example Telegram Parsing Request

```json
{
  "channel_username": "durov",
  "limit": 5
}
```

## Example Manual Generation Request

```json
{
  "news_id": 1
}
```

## Notes

- `.env` is ignored by Git and must not be committed.
- Telethon creates `.session` files. They are ignored by Git.
- OpenAI API generation requires a valid API key and active API credits.
- Celery Beat is configured to run RSS parsing every 30 minutes.
- On Windows, Celery worker is started with `--pool=solo`.
- `TELEGRAM_TARGET_CHANNEL` must point to a Telegram channel where your account has admin permissions.

## Next Steps

- Improve duplicate detection for Telegram messages
- Load scheduled RSS sources from the `sources` table
- Add automatic post generation pipeline
- Add automatic Telegram publishing pipeline
- Add more detailed logging for all background tasks