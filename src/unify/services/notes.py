from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, col, select

from unify.models import Note
from unify.schemas import NoteCreate, NoteUpdate


def list_notes(db: Session, *, include_deleted: bool = False) -> list[Note]:
    statement = select(Note)
    if not include_deleted:
        statement = statement.where(col(Note.deleted_at).is_(None))
    statement = statement.order_by(col(Note.created_at).desc())
    return list(db.exec(statement).all())


def get_note(db: Session, note_id: UUID) -> Note | None:
    note = db.get(Note, note_id)
    if note is None or note.deleted_at is not None:
        return None
    return note


def create_note(db: Session, data: NoteCreate) -> Note:
    note = Note.model_validate(data)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, note_id: UUID, data: NoteUpdate) -> Note | None:
    note = get_note(db, note_id)
    if note is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(note, field, value)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: UUID, *, hard: bool = False) -> bool:
    note = db.get(Note, note_id)
    if note is None or (note.deleted_at is not None and not hard):
        return False
    if hard:
        db.delete(note)
    else:
        note.deleted_at = datetime.now(UTC)
        db.add(note)
    db.commit()
    return True
