from collections.abc import Generator
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from unify.models import Bookmark, Note


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


def test_note_defaults_and_timezone_aware_timestamps(session: Session) -> None:
    note = Note(title="Test note")
    session.add(note)
    session.commit()

    saved = session.get(Note, note.id)

    assert saved is not None
    assert isinstance(saved.id, UUID)
    assert saved.tags == []
    assert saved.created_at is not None
    assert saved.created_at.tzinfo is not None
    assert saved.created_at.utcoffset() == timedelta(0)


def test_bookmark_round_trip(session: Session) -> None:
    bookmark = Bookmark(url="https://example.com")
    session.add(bookmark)
    session.commit()

    saved = session.get(Bookmark, bookmark.id)

    assert saved is not None
    assert saved.url == "https://example.com"


def test_note_updated_at_is_not_before_created_at(session: Session) -> None:
    notes = [Note(title="First"), Note(title="Second")]
    session.add_all(notes)
    session.commit()

    assert all(note.updated_at >= note.created_at for note in notes)


def test_note_soft_delete(session: Session) -> None:
    note = Note(title="Deleted note")
    session.add(note)
    session.commit()

    note.deleted_at = note.updated_at
    session.add(note)
    session.commit()

    saved = session.get(Note, note.id)

    assert saved is not None
    assert saved.deleted_at is not None
