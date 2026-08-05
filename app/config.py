from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Telegram News Bot"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aibot"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    redis_url: str = "redis://localhost:6379/0"
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_name: str = "aibot_session"
    telegram_target_channel: str = "me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")




settings = Settings()