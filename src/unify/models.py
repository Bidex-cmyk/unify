from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class _UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Note(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(index=True, max_length=200)
    body: str = ""
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(_UTCDateTime(), nullable=False, default=_utcnow),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(_UTCDateTime(), nullable=False, default=_utcnow, onupdate=_utcnow),
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(_UTCDateTime(), nullable=True)
    )


class Bookmark(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    url: str = Field(sa_type=String(2048), unique=True, index=True, max_length=2048)
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(_UTCDateTime(), nullable=False, default=_utcnow),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(_UTCDateTime(), nullable=False, default=_utcnow, onupdate=_utcnow),
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(_UTCDateTime(), nullable=True)
    )
