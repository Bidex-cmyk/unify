from datetime import timedelta
from uuid import UUID

from sqlmodel import Session

from unify.models import Bookmark, Note


def test_note_defaults_and_timezone_aware_timestamps(db_session: Session) -> None:
    note = Note(title="Test note")
    db_session.add(note)
    db_session.commit()

    saved = db_session.get(Note, note.id)

    assert saved is not None
    assert isinstance(saved.id, UUID)
    assert saved.tags == []
    assert saved.created_at is not None
    assert saved.created_at.tzinfo is not None
    assert saved.created_at.utcoffset() == timedelta(0)


def test_bookmark_round_trip(db_session: Session) -> None:
    bookmark = Bookmark(url="https://example.com")
    db_session.add(bookmark)
    db_session.commit()

    saved = db_session.get(Bookmark, bookmark.id)

    assert saved is not None
    assert saved.url == "https://example.com"


def test_note_updated_at_is_not_before_created_at(db_session: Session) -> None:
    notes = [Note(title="First"), Note(title="Second")]
    db_session.add_all(notes)
    db_session.commit()

    assert all(note.updated_at >= note.created_at for note in notes)


def test_note_soft_delete(db_session: Session) -> None:
    note = Note(title="Deleted note")
    db_session.add(note)
    db_session.commit()

    note.deleted_at = note.updated_at
    db_session.add(note)
    db_session.commit()

    saved = db_session.get(Note, note.id)

    assert saved is not None
    assert saved.deleted_at is not None
