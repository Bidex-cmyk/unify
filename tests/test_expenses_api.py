from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def _create_expense(
    client: TestClient,
    auth_headers: dict[str, str],
    *,
    amount_minor: int = 1250,
    category: str = "food",
    occurred_at: datetime | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "amount_minor": amount_minor,
        "category": category,
    }
    if occurred_at is not None:
        payload["occurred_at"] = occurred_at.isoformat()
    response = client.post("/api/expenses", headers=auth_headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_expense_returns_minor_units_and_uppercase_currency(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/expenses",
        headers=auth_headers,
        json={"amount_minor": 100, "currency": "usd"},
    )

    assert response.status_code == 201
    assert response.json()["amount_minor"] == 100
    assert response.json()["currency"] == "USD"


@pytest.mark.parametrize("amount_minor", [0, -100])
def test_create_rejects_non_positive_amount(
    client: TestClient,
    auth_headers: dict[str, str],
    amount_minor: int,
) -> None:
    response = client.post(
        "/api/expenses",
        headers=auth_headers,
        json={"amount_minor": amount_minor},
    )

    assert response.status_code == 422


def test_list_expenses_newest_first(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    now = datetime.now(UTC)
    _create_expense(client, auth_headers, category="older", occurred_at=now - timedelta(days=1))
    _create_expense(client, auth_headers, category="newer", occurred_at=now)

    response = client.get("/api/expenses", headers=auth_headers)

    assert [entry["category"] for entry in response.json()] == ["newer", "older"]


def test_since_and_until_filters(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    now = datetime.now(UTC)
    _create_expense(client, auth_headers, category="before", occurred_at=now - timedelta(days=2))
    _create_expense(client, auth_headers, category="inside", occurred_at=now - timedelta(days=1))
    _create_expense(client, auth_headers, category="after", occurred_at=now)

    response = client.get(
        "/api/expenses",
        headers=auth_headers,
        params={"since": now - timedelta(days=1, hours=1), "until": now - timedelta(hours=1)},
    )

    assert [entry["category"] for entry in response.json()] == ["inside"]


def test_patch_updates_only_provided_fields(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    expense = _create_expense(client, auth_headers, amount_minor=1250)

    response = client.patch(
        f"/api/expenses/{expense['id']}",
        headers=auth_headers,
        json={"note": "updated"},
    )

    assert response.status_code == 200
    assert response.json()["note"] == "updated"
    assert response.json()["amount_minor"] == 1250


def test_soft_delete_hides_expense_unless_including_deleted(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    expense = _create_expense(client, auth_headers)

    assert client.delete(f"/api/expenses/{expense['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/expenses/{expense['id']}", headers=auth_headers).status_code == 404
    included = client.get(
        "/api/expenses",
        headers=auth_headers,
        params={"include_deleted": True},
    )
    assert [entry["id"] for entry in included.json()] == [expense["id"]]


def test_hard_delete_removes_expense(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    expense = _create_expense(client, auth_headers)

    response = client.delete(
        f"/api/expenses/{expense['id']}",
        headers=auth_headers,
        params={"hard": True},
    )
    listing = client.get(
        "/api/expenses",
        headers=auth_headers,
        params={"include_deleted": True},
    )

    assert response.status_code == 204
    assert listing.json() == []


def test_summary_returns_integer_totals_for_current_month(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    now = datetime.now(UTC)
    _create_expense(client, auth_headers, amount_minor=1200, category="food", occurred_at=now)
    _create_expense(client, auth_headers, amount_minor=300, category="food", occurred_at=now)
    _create_expense(client, auth_headers, amount_minor=500, category="travel", occurred_at=now)

    response = client.get(
        "/api/expenses/summary",
        headers=auth_headers,
        params={"month": now.strftime("%Y-%m")},
    )

    assert response.json() == {
        "month": now.strftime("%Y-%m"),
        "total_minor": 2000,
        "by_category": {"food": 1500, "travel": 500},
    }


def test_empty_month_summary_is_zero(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/expenses/summary",
        headers=auth_headers,
        params={"month": "1999-01"},
    )

    assert response.json() == {"month": "1999-01", "total_minor": 0, "by_category": {}}


def test_invalid_month_returns_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/api/expenses/summary",
        headers=auth_headers,
        params={"month": "bad"},
    )

    assert response.status_code == 422


def test_summary_excludes_soft_deleted_expenses(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    now = datetime.now(UTC)
    expense = _create_expense(client, auth_headers, amount_minor=800, occurred_at=now)
    client.delete(f"/api/expenses/{expense['id']}", headers=auth_headers)

    response = client.get(
        "/api/expenses/summary",
        headers=auth_headers,
        params={"month": now.strftime("%Y-%m")},
    )

    assert response.json()["total_minor"] == 0


def test_summary_month_boundaries(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    now = datetime.now(UTC)
    start = datetime(now.year, now.month, 1, tzinfo=UTC)
    previous_month = start - timedelta(seconds=1)
    _create_expense(client, auth_headers, amount_minor=700, occurred_at=start)
    _create_expense(client, auth_headers, amount_minor=900, occurred_at=previous_month)

    response = client.get(
        "/api/expenses/summary",
        headers=auth_headers,
        params={"month": start.strftime("%Y-%m")},
    )

    assert response.json()["total_minor"] == 700


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/api/expenses", {}),
        ("get", "/api/expenses/summary?month=2026-10", {}),
        ("post", "/api/expenses", {"json": {"amount_minor": 500}}),
        ("get", f"/api/expenses/{uuid4()}", {}),
        ("patch", f"/api/expenses/{uuid4()}", {"json": {"note": "test"}}),
        ("delete", f"/api/expenses/{uuid4()}", {}),
    ],
)
def test_expense_routes_require_auth(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict[str, object],
) -> None:
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
