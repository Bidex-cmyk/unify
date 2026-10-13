from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = ""
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    tags: list[str] | None = None


class NoteRead(BaseModel):
    id: UUID
    title: str
    body: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookmarkCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class BookmarkUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class BookmarkRead(BaseModel):
    id: UUID
    url: str
    title: str
    description: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
