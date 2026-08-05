from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Telegram News Bot"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aibot"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")




settings = Settings()