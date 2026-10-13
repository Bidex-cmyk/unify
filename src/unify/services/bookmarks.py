from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, col, select

from unify.models import Bookmark
from unify.schemas import BookmarkCreate, BookmarkUpdate


def list_bookmarks(db: Session, *, include_deleted: bool = False) -> list[Bookmark]:
    statement = select(Bookmark)
    if not include_deleted:
        statement = statement.where(col(Bookmark.deleted_at).is_(None))
    statement = statement.order_by(col(Bookmark.created_at).desc())
    return list(db.exec(statement).all())


def get_bookmark(db: Session, bookmark_id: UUID) -> Bookmark | None:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None or bookmark.deleted_at is not None:
        return None
    return bookmark


def create_bookmark(db: Session, data: BookmarkCreate) -> Bookmark:
    bookmark = Bookmark.model_validate(data)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def update_bookmark(db: Session, bookmark_id: UUID, data: BookmarkUpdate) -> Bookmark | None:
    bookmark = get_bookmark(db, bookmark_id)
    if bookmark is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(bookmark, field, value)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


def delete_bookmark(db: Session, bookmark_id: UUID, *, hard: bool = False) -> bool:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None or (bookmark.deleted_at is not None and not hard):
        return False
    if hard:
        db.delete(bookmark)
    else:
        bookmark.deleted_at = datetime.now(UTC)
        db.add(bookmark)
    db.commit()
    return True


def apply_metadata(db: Session, bookmark_id: UUID, title: str, description: str) -> None:
    bookmark = db.get(Bookmark, bookmark_id)
    if bookmark is None:
        return
    if not bookmark.title and title:
        bookmark.title = title
    if not bookmark.description and description:
        bookmark.description = description
    db.add(bookmark)
    db.commit()
