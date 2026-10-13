from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlmodel import Session
from starlette.responses import HTMLResponse

from unify.db import get_session
from unify.schemas import NoteCreate
from unify.services import notes
from unify.ui.auth import require_ui_session
from unify.ui.forms import parse_tags
from unify.ui.templating import templates

router = APIRouter(
    prefix="/ui/notes",
    tags=["ui"],
    dependencies=[Depends(require_ui_session)],
)


@router.get("")
def list_notes_ui(request: Request, db: Session = Depends(get_session)) -> Response:  # noqa: B008
    return templates.TemplateResponse(
        request=request,
        name="notes.html",
        context={"notes": notes.list_notes(db)},
    )


@router.post("")
def create_note_ui(
    request: Request,
    title: str = Form(""),
    body: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not title.strip():
        return HTMLResponse(
            '<p class="error">A title is required.</p>',
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    note = notes.create_note(db, NoteCreate(title=title, body=body, tags=parse_tags(tags)))
    return templates.TemplateResponse(
        request=request,
        name="partials/_note_row.html",
        context={"note": note},
    )


@router.delete("/{note_id}")
def delete_note_ui(note_id: UUID, db: Session = Depends(get_session)) -> Response:  # noqa: B008
    if not notes.delete_note(db, note_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return Response(status_code=status.HTTP_200_OK)
