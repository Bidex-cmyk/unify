import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from unify.db import get_session, session_scope
from unify.schemas import BookmarkCreate, BookmarkRead, BookmarkUpdate
from unify.services import bookmarks, fetch_meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


async def _hydrate(bookmark_id: UUID, url: str) -> None:
    try:
        title, description = await fetch_meta.fetch_metadata(url)
        if title or description:
            with session_scope() as db:
                bookmarks.apply_metadata(db, bookmark_id, title, description)
    except Exception:
        logger.exception("bookmark hydrate failed")


@router.get("", response_model=list[BookmarkRead])
def list_bookmarks(
    include_deleted: bool = False,
    db: Session = Depends(get_session),  # noqa: B008
) -> list[BookmarkRead]:
    return bookmarks.list_bookmarks(db, include_deleted=include_deleted)


@router.get("/{bookmark_id}", response_model=BookmarkRead)
def get_bookmark(
    bookmark_id: UUID,
    db: Session = Depends(get_session),  # noqa: B008
) -> BookmarkRead:
    bookmark = bookmarks.get_bookmark(db, bookmark_id)
    if bookmark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return bookmark


@router.post("", response_model=BookmarkRead, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    data: BookmarkCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_session),  # noqa: B008
) -> BookmarkRead:
    try:
        bookmark = bookmarks.create_bookmark(db, data)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Bookmark URL already exists"
        ) from exc
    background.add_task(_hydrate, bookmark.id, bookmark.url)
    return bookmark


@router.patch("/{bookmark_id}", response_model=BookmarkRead)
def update_bookmark(
    bookmark_id: UUID,
    data: BookmarkUpdate,
    db: Session = Depends(get_session),  # noqa: B008
) -> BookmarkRead:
    bookmark = bookmarks.update_bookmark(db, bookmark_id, data)
    if bookmark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: UUID,
    hard: bool = False,
    db: Session = Depends(get_session),  # noqa: B008
) -> Response:
    if not bookmarks.delete_bookmark(db, bookmark_id, hard=hard):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
