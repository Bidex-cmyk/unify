from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from unify.db import get_session
from unify.schemas import NoteCreate, NoteRead, NoteUpdate
from unify.services import notes

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
def list_notes(
    include_deleted: bool = False,
    db: Session = Depends(get_session),  # noqa: B008
) -> list[NoteRead]:
    return notes.list_notes(db, include_deleted=include_deleted)


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: UUID, db: Session = Depends(get_session)) -> NoteRead:  # noqa: B008
    note = notes.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(data: NoteCreate, db: Session = Depends(get_session)) -> NoteRead:  # noqa: B008
    return notes.create_note(db, data)


@router.patch("/{note_id}", response_model=NoteRead)
def update_note(
    note_id: UUID,
    data: NoteUpdate,
    db: Session = Depends(get_session),  # noqa: B008
) -> NoteRead:
    note = notes.update_note(db, note_id, data)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: UUID,
    hard: bool = False,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not notes.delete_note(db, note_id, hard=hard):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
