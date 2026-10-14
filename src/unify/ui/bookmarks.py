from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from starlette.responses import HTMLResponse

from unify.db import get_session
from unify.routers.bookmarks import _hydrate
from unify.schemas import BookmarkCreate
from unify.services import bookmarks
from unify.ui.auth import require_ui_session
from unify.ui.forms import parse_tags
from unify.ui.templating import templates

_HYDRATE_POLL_LIMIT = 5

router = APIRouter(
    prefix="/ui/bookmarks",
    tags=["ui"],
    dependencies=[Depends(require_ui_session)],
)


@router.get("")
def list_bookmarks_ui(
    request: Request,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="bookmarks.html",
        context={"bookmarks": bookmarks.list_bookmarks(db)},
    )


@router.post("")
def create_bookmark_ui(
    request: Request,
    background: BackgroundTasks,
    url: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not url.strip():
        return HTMLResponse(
            '<p class="error">A URL is required.</p>',
            status_code=422,
        )
    try:
        bookmark = bookmarks.create_bookmark(
            db,
            BookmarkCreate(url=url, tags=parse_tags(tags)),
        )
    except IntegrityError:
        db.rollback()
        return HTMLResponse(
            '<p class="error">That URL is already bookmarked.</p>',
            status_code=409,
        )
    background.add_task(_hydrate, bookmark.id, bookmark.url)
    return templates.TemplateResponse(
        request=request,
        name="partials/_bookmark_row.html",
        context={"bm": bookmark, "attempt": 0, "bm_poll": True},
    )


@router.get("/{bookmark_id}")
def get_bookmark_row_ui(
    request: Request,
    bookmark_id: UUID,
    attempt: int = 0,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    bookmark = bookmarks.get_bookmark(db, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return templates.TemplateResponse(
        request=request,
        name="partials/_bookmark_row.html",
        context={
            "bm": bookmark,
            "attempt": attempt,
            # Keep polling until the background fetch fills the title in, up to a limit.
            "bm_poll": not bookmark.title and attempt < _HYDRATE_POLL_LIMIT,
        },
    )


@router.delete("/{bookmark_id}")
def delete_bookmark_ui(
    bookmark_id: UUID,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not bookmarks.delete_bookmark(db, bookmark_id):
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return Response(status_code=200)
