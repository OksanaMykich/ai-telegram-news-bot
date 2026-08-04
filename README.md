# AI Telegram News Bot

A FastAPI service for collecting news, filtering relevant items, generating Telegram posts with AI, and publishing them to a Telegram channel.

## Current Features

- FastAPI application
- Swagger API documentation at `/docs`
- PostgreSQL database connection
- Alembic migrations
- Source CRUD API
- Keyword CRUD API
- News item test API
- Post history test API

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn

## Project Structure

```text
app/
├── api/
│   ├── endpoints.py
│   └── schemas.py
├── config.py
├── database.py
├── main.py
└── models.py
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
APP_NAME=AI Telegram News Bot
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aibot
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

## Running the App

```powershell
uvicorn app.main:app --reload
```

Open Swagger documentation:

```text
http://127.0.0.1:8000/docs
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

POST   /api/posts/
GET    /api/posts/
```

## Next Steps

- Split API endpoints into separate files
- Add site news parser
- Add news filtering logic
- Add AI post generation
- Add Celery and Redis
- Add Telegram publishing with Telethon