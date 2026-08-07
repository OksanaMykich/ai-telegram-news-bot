from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceBase(BaseModel):
    type: str
    name: str
    url: str
    enabled: bool = True


class SourceCreate(SourceBase):
    pass

class SourceUpdate(SourceBase):
    pass

class SourceRead(SourceBase):
    id: int

    class Config:
        from_attributes = True

class KeywordBase(BaseModel):
    word: str


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(KeywordBase):
    pass


class KeywordRead(KeywordBase):
    id: int

    class Config:
        from_attributes = True

class NewsItemBase(BaseModel):
    title: str
    url: str | None = None
    summary: str
    source: str
    published_at: datetime
    raw_text: str | None = None


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemRead(NewsItemBase):
    id: int

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    news_id: int
    generated_text: str
    published_at: datetime | None = None
    status: str = "new"


class PostCreate(PostBase):
    pass


class PostRead(PostBase):
    id: int

    class Config:
        from_attributes = True

class RSSParseRequest(BaseModel):
    source_name: str
    feed_url: str

class GeneratePostRequest(BaseModel):
    news_id: int

class TelegramParseRequest(BaseModel):
    channel_username: str
    limit: int = 10

class ErrorLogRead(BaseModel):
    id: int
    message: str
    source: str | None = None
    task_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)