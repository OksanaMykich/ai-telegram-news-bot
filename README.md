# AI Telegram News Bot

FastAPI service for collecting news from RSS feeds and public Telegram channels, filtering relevant items, generating AI-based Telegram posts, and publishing them to a Telegram channel on schedule.

## Features

- FastAPI application with Swagger documentation
- PostgreSQL database with Alembic migrations
- CRUD API for news sources
- CRUD API for keywords
- News item history API
- Generated post history API
- Error logs API
- Celery task monitoring API
- RSS news parsing
- Public Telegram channel parsing with Telethon
- Keyword-based news filtering
- Source-based filtering through enabled sources
- Source language filtering
- Duplicate protection for news and posts
- Manual AI post generation with OpenAI API
- OpenAI error handling
- Telegram publishing with Telethon
- Redis and Celery background tasks
- Celery Beat scheduled full news pipeline
- Full pipeline: parse enabled sources -> generate AI posts -> publish generated posts
- Logging for API actions and Celery tasks

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
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
│   ├── generator.py
│   └── openai_client.py
├── api/
│   ├── endpoints/
│   │   ├── error_logs.py
│   │   ├── generate.py
│   │   ├── keywords.py
│   │   ├── news.py
│   │   ├── pipeline.py
│   │   ├── posts.py
│   │   ├── sources.py
│   │   └── tasks.py
│   ├── router.py
│   └── schemas.py
├── news_parser/
│   ├── sites.py
│   └── telegram.py
├── telegram/
│   └── publisher.py
├── config.py
├── database.py
├── error_logger.py
├── logging_config.py
├── main.py
├── models.py
├── tasks.py
└── utils.py
```

## Environment Variables

Create a `.env` file based on `.env.example`.

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

## Database Setup

Create a PostgreSQL database named:

```text
aibot
```

Run migrations:

```powershell
alembic upgrade head
```

## Redis Setup

Start Docker Desktop first.

If the Redis container already exists:

```powershell
docker start aibot-redis
```

If the Redis container does not exist yet:

```powershell
docker run --name aibot-redis -p 6379:6379 -d redis:7
```

Check that Redis is running:

```powershell
docker ps
```

## Running the Application

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

Open Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Running Background Services

Start Celery worker:

```powershell
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

Start Celery Beat:

```powershell
celery -A celery_worker.celery_app beat --loglevel=info
```

Celery Beat runs the full news pipeline every 30 minutes:

```text
parse enabled sources -> generate AI posts -> publish generated posts
```

On Windows, Celery worker should be started with `--pool=solo`.

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
POST   /api/generate/task
POST   /api/generate/task/bulk

POST   /api/posts/
GET    /api/posts/
POST   /api/posts/{post_id}/publish
POST   /api/posts/{post_id}/publish-task
POST   /api/posts/publish-task/bulk

POST   /api/pipeline/run

GET    /api/tasks/{task_id}

GET    /api/error-logs/
```

## Example Sources

RSS source:

```json
{
  "type": "site",
  "name": "BBC News RSS",
  "url": "https://feeds.bbci.co.uk/news/rss.xml",
  "enabled": true,
  "language": "en"
}
```

Telegram source:

```json
{
  "type": "tg",
  "name": "Durov",
  "url": "durov",
  "enabled": true,
  "language": "en"
}
```

## Pipeline

Run the full pipeline manually through Swagger:

```text
POST /api/pipeline/run
```

Parameters:

```text
generation_limit: maximum number of news items for AI generation
publishing_limit: maximum number of generated posts to publish
language: optional source language filter, for example en or uk
```

If `language` is empty, the pipeline uses all enabled sources.


## Notes

- `.env` must not be committed to Git.
- Telethon creates `.session` files. They must not be committed.
- OpenAI generation requires a valid API key and active API credits.
- Celery Beat uses only sources where `enabled = true`.
- RSS sources must use a direct RSS feed URL.
- Telegram sources use public channel usernames.
- `TELEGRAM_TARGET_CHANNEL` must be a Telegram channel where the account has admin permissions.
- If OpenAI credits are missing, generation tasks return a controlled failed status instead of crashing the application.