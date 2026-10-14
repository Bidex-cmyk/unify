from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ExpenseCreate(BaseModel):
    amount_minor: int = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: str = Field(default="uncategorized", max_length=50)
    note: str = ""
    occurred_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class ExpenseUpdate(BaseModel):
    amount_minor: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category: str | None = Field(default=None, max_length=50)
    note: str | None = None
    occurred_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None


class ExpenseRead(BaseModel):
    id: UUID
    amount_minor: int
    currency: str
    category: str
    note: str
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
