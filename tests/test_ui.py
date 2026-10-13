from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from unify.config import settings
from unify.main import create_app
from unify.routers import bookmarks as bookmarks_router
from unify.services import fetch_meta
from unify.sessions import COOKIE_NAME, sign_session


@pytest.fixture
def ui_client(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setattr(settings, "session_secret", "ui-test-secret")
    monkeypatch.setattr(settings, "ui_password", "ui-test-password")
    client.cookies.set(COOKIE_NAME, sign_session())
    return client


def test_landing_page_links_to_collections(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "/ui/notes" in response.text
    assert "/ui/bookmarks" in response.text


def test_notes_page_empty_state(ui_client: TestClient) -> None:
    response = ui_client.get("/ui/notes")

    assert response.status_code == 200
    assert "Notes" in response.text
    assert "No notes yet." in response.text


def test_note_create_and_delete_round_trip(ui_client: TestClient) -> None:
    created = ui_client.post(
        "/ui/notes",
        data={"title": "UI note", "body": "Note body", "tags": "one, two,, "},
    )

    assert created.status_code == 200
    assert "UI note" in created.text
    assert "#one" in created.text
    assert "#two" in created.text
    note_id = created.text.split('id="note-', maxsplit=1)[1].split('"', maxsplit=1)[0]
    listing = ui_client.get("/ui/notes")
    deleted = ui_client.delete(f"/ui/notes/{note_id}")
    listing_after_delete = ui_client.get("/ui/notes")

    assert "UI note" in listing.text
    assert deleted.status_code == 200
    assert "UI note" not in listing_after_delete.text


def test_note_title_is_html_escaped(ui_client: TestClient) -> None:
    response = ui_client.post(
        "/ui/notes",
        data={"title": "<script>alert(1)</script>", "body": ""},
    )

    assert response.status_code == 200
    assert "&lt;script&gt;" in response.text
    assert "<script>" not in response.text


@pytest.fixture
def stub_bookmark_metadata(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
) -> None:
    async def fetch_metadata(url: str) -> tuple[str, str]:
        return "Example", "desc"

    @contextmanager
    def test_session_scope() -> Generator[Session, None, None]:
        yield db_session

    monkeypatch.setattr(fetch_meta, "fetch_metadata", fetch_metadata)
    monkeypatch.setattr(bookmarks_router, "session_scope", test_session_scope)


def test_bookmark_create_and_delete_round_trip(
    ui_client: TestClient,
    stub_bookmark_metadata: None,
) -> None:
    created = ui_client.post(
        "/ui/bookmarks",
        data={"url": "https://example.com/ui-test", "tags": "reading, saved"},
    )

    assert created.status_code == 200
    assert "https://example.com/ui-test" in created.text
    assert "#reading" in created.text
    bookmark_id = created.text.split('id="bm-', maxsplit=1)[1].split('"', maxsplit=1)[0]
    listing = ui_client.get("/ui/bookmarks")
    deleted = ui_client.delete(f"/ui/bookmarks/{bookmark_id}")
    listing_after_delete = ui_client.get("/ui/bookmarks")

    assert "https://example.com/ui-test" in listing.text
    assert deleted.status_code == 200
    assert "https://example.com/ui-test" not in listing_after_delete.text


def test_api_still_requires_auth(client: TestClient) -> None:
    response = client.get("/api/notes")

    assert response.status_code == 401


def test_ui_routes_are_not_registered_outside_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "environment", "prod")

    routes = create_app().openapi()["paths"]

    assert "/" not in routes
    assert "/ui/notes" not in routes
    assert "/ui/bookmarks" not in routes
