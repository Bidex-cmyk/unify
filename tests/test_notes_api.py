from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient


def _create_note(
    client: TestClient,
    auth_headers: dict[str, str],
    *,
    title: str = "hello",
    body: str = "",
) -> dict[str, object]:
    response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={"title": title, "body": body, "tags": ["a"]},
    )
    assert response.status_code == 201
    return response.json()


def test_create_note_returns_uuid_tags_and_aware_timestamp(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/notes",
        headers=auth_headers,
        json={"title": "hello", "tags": ["a"]},
    )

    assert response.status_code == 201
    data = response.json()
    assert UUID(data["id"])
    assert data["tags"] == ["a"]
    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    assert created_at.tzinfo is not None


def test_list_notes_returns_newest_first(client: TestClient, auth_headers: dict[str, str]) -> None:
    _create_note(client, auth_headers, title="older")
    _create_note(client, auth_headers, title="newer")

    response = client.get("/api/notes", headers=auth_headers)

    assert response.status_code == 200
    assert [note["title"] for note in response.json()] == ["newer", "older"]


def test_get_note_and_unknown_uuid(client: TestClient, auth_headers: dict[str, str]) -> None:
    note = _create_note(client, auth_headers)

    response = client.get(f"/api/notes/{note['id']}", headers=auth_headers)
    unknown = client.get(f"/api/notes/{uuid4()}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == note["id"]
    assert unknown.status_code == 404


def test_patch_only_updates_provided_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    note = _create_note(client, auth_headers, body="keep this body")

    response = client.patch(
        f"/api/notes/{note['id']}",
        headers=auth_headers,
        json={"title": "updated"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "updated"
    assert response.json()["body"] == "keep this body"


def test_soft_delete_hides_note_unless_including_deleted(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    note = _create_note(client, auth_headers)

    deleted = client.delete(f"/api/notes/{note['id']}", headers=auth_headers)
    hidden = client.get(f"/api/notes/{note['id']}", headers=auth_headers)
    included = client.get(
        "/api/notes",
        headers=auth_headers,
        params={"include_deleted": True},
    )

    assert deleted.status_code == 204
    assert hidden.status_code == 404
    assert [entry["id"] for entry in included.json()] == [note["id"]]


def test_hard_delete_removes_note_permanently(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    note = _create_note(client, auth_headers)

    response = client.delete(
        f"/api/notes/{note['id']}",
        headers=auth_headers,
        params={"hard": True},
    )
    included = client.get(
        "/api/notes",
        headers=auth_headers,
        params={"include_deleted": True},
    )

    assert response.status_code == 204
    assert included.json() == []


def test_get_note_rejects_malformed_uuid(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/notes/bad-uuid", headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/api/notes", {}),
        ("get", f"/api/notes/{uuid4()}", {}),
        ("post", "/api/notes", {"json": {"title": "auth required"}}),
        ("patch", f"/api/notes/{uuid4()}", {"json": {"title": "auth required"}}),
        ("delete", f"/api/notes/{uuid4()}", {}),
    ],
)
def test_notes_routes_require_auth(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
