from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from unify.config import settings
from unify.main import create_app
from unify.routers import bookmarks as bookmarks_router
from unify.services import bookmarks, fetch_meta
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
    assert "/ui/expenses" in response.text
    assert "notes, bookmarks, and expenses" in response.text
    assert response.text.count('class="card"') == 3


def test_logout_button_is_hidden_without_a_session(client: TestClient) -> None:
    assert "Log out" not in client.get("/").text
    assert "Log out" not in client.get("/login").text


def test_logout_button_is_shown_with_a_session(ui_client: TestClient) -> None:
    assert "Log out" in ui_client.get("/").text
    assert "Log out" in ui_client.get("/ui/notes").text


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


@pytest.fixture
def unfetchable_bookmark_metadata(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
) -> None:
    async def fetch_metadata(url: str) -> tuple[str, str]:
        return "", ""

    @contextmanager
    def test_session_scope() -> Generator[Session, None, None]:
        yield db_session

    monkeypatch.setattr(fetch_meta, "fetch_metadata", fetch_metadata)
    monkeypatch.setattr(bookmarks_router, "session_scope", test_session_scope)


def test_bookmark_row_polls_until_the_title_is_hydrated(
    ui_client: TestClient,
    db_session: Session,
    unfetchable_bookmark_metadata: None,
) -> None:
    created = ui_client.post("/ui/bookmarks", data={"url": "https://example.com/polling"})
    bookmark_id = created.text.split('id="bm-', maxsplit=1)[1].split('"', maxsplit=1)[0]

    assert 'hx-trigger="load delay:1200ms"' in created.text
    assert f"/ui/bookmarks/{bookmark_id}?attempt=1" in created.text

    still_empty = ui_client.get(f"/ui/bookmarks/{bookmark_id}?attempt=2")
    assert "?attempt=3" in still_empty.text
    assert 'hx-trigger="load delay:1200ms"' in still_empty.text

    bookmark = bookmarks.get_bookmark(db_session, UUID(bookmark_id))
    assert bookmark is not None
    bookmark.title = "Hydrated title"
    db_session.add(bookmark)
    db_session.commit()

    hydrated = ui_client.get(f"/ui/bookmarks/{bookmark_id}?attempt=3")
    assert "Hydrated title" in hydrated.text
    assert "hx-trigger" not in hydrated.text


def test_bookmark_row_stops_polling_after_the_attempt_limit(
    ui_client: TestClient,
    unfetchable_bookmark_metadata: None,
) -> None:
    created = ui_client.post("/ui/bookmarks", data={"url": "https://example.com/tired"})
    bookmark_id = created.text.split('id="bm-', maxsplit=1)[1].split('"', maxsplit=1)[0]

    exhausted = ui_client.get(f"/ui/bookmarks/{bookmark_id}?attempt=5")

    assert "hx-trigger" not in exhausted.text


def test_bookmark_row_404s_for_unknown_id(ui_client: TestClient) -> None:
    response = ui_client.get("/ui/bookmarks/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_bookmark_list_does_not_poll_on_page_load(
    ui_client: TestClient,
    unfetchable_bookmark_metadata: None,
) -> None:
    ui_client.post("/ui/bookmarks", data={"url": "https://example.com/no-poll"})

    listing = ui_client.get("/ui/bookmarks")

    assert "no-poll" in listing.text
    assert "hx-trigger" not in listing.text


def test_ui_routes_are_not_registered_outside_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "environment", "prod")

    routes = create_app().openapi()["paths"]

    assert "/" not in routes
    assert "/ui/notes" not in routes
    assert "/ui/bookmarks" not in routes
