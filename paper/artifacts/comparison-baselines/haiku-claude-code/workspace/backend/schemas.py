from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TagBase(BaseModel):
    name: str


class TagResponse(TagBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class NoteUpdate(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
