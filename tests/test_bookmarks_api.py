from collections.abc import Generator
from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from unify.routers import bookmarks as bookmark_router
from unify.services import fetch_meta


@pytest.fixture
def mock_metadata(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
) -> None:
    async def fetch_metadata(url: str) -> tuple[str, str]:
        return "Example", "desc"

    @contextmanager
    def test_session_scope() -> Generator[Session, None, None]:
        yield db_session

    monkeypatch.setattr(fetch_meta, "fetch_metadata", fetch_metadata)
    monkeypatch.setattr(bookmark_router, "session_scope", test_session_scope)


def _create_bookmark(
    client: TestClient,
    auth_headers: dict[str, str],
    *,
    url: str = "https://example.com",
) -> dict[str, object]:
    response = client.post(
        "/api/bookmarks",
        headers=auth_headers,
        json={"url": url},
    )
    assert response.status_code == 201
    return response.json()


def test_create_bookmark_hydrates_metadata(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    response = client.post(
        "/api/bookmarks",
        headers=auth_headers,
        json={"url": "https://example.com"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == ""
    assert data["url"] == "https://example.com"
    hydrated = client.get(f"/api/bookmarks/{data['id']}", headers=auth_headers)
    assert hydrated.json()["title"] == "Example"
    assert hydrated.json()["description"] == "desc"


def test_duplicate_url_returns_conflict(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    _create_bookmark(client, auth_headers)

    response = client.post(
        "/api/bookmarks",
        headers=auth_headers,
        json={"url": "https://example.com"},
    )

    assert response.status_code == 409


def test_list_and_get_bookmarks(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    bookmark = _create_bookmark(client, auth_headers)

    listing = client.get("/api/bookmarks", headers=auth_headers)
    fetched = client.get(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    missing = client.get(f"/api/bookmarks/{uuid4()}", headers=auth_headers)

    assert [item["id"] for item in listing.json()] == [bookmark["id"]]
    assert fetched.status_code == 200
    assert fetched.json()["id"] == bookmark["id"]
    assert missing.status_code == 404


def test_patch_updates_title_without_changing_url(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    bookmark = _create_bookmark(client, auth_headers)

    response = client.patch(
        f"/api/bookmarks/{bookmark['id']}",
        headers=auth_headers,
        json={"title": "Updated"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["url"] == "https://example.com"


def test_soft_delete_hides_bookmark_unless_including_deleted(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    bookmark = _create_bookmark(client, auth_headers)

    deleted = client.delete(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    hidden = client.get(f"/api/bookmarks/{bookmark['id']}", headers=auth_headers)
    included = client.get(
        "/api/bookmarks",
        headers=auth_headers,
        params={"include_deleted": True},
    )

    assert deleted.status_code == 204
    assert hidden.status_code == 404
    assert [item["id"] for item in included.json()] == [bookmark["id"]]


def test_hard_delete_removes_bookmark_permanently(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_metadata: None,
) -> None:
    bookmark = _create_bookmark(client, auth_headers)

    deleted = client.delete(
        f"/api/bookmarks/{bookmark['id']}",
        headers=auth_headers,
        params={"hard": True},
    )
    included = client.get(
        "/api/bookmarks",
        headers=auth_headers,
        params={"include_deleted": True},
    )

    assert deleted.status_code == 204
    assert included.json() == []


def test_bookmark_bad_uuid_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/api/bookmarks/bad-uuid", headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/api/bookmarks", {}),
        ("get", f"/api/bookmarks/{uuid4()}", {}),
        ("post", "/api/bookmarks", {"json": {"url": "https://example.com"}}),
        ("patch", f"/api/bookmarks/{uuid4()}", {"json": {"title": "auth required"}}),
        ("delete", f"/api/bookmarks/{uuid4()}", {}),
    ],
)
def test_bookmark_routes_require_auth(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
