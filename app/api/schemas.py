from pydantic import BaseModel


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