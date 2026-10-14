import pytest
from fastapi.testclient import TestClient

from unify.config import settings
from unify.sessions import COOKIE_NAME, sign_session


@pytest.fixture
def authenticated_ui_client(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setattr(settings, "session_secret", "expense-ui-test-secret")
    client.cookies.set(COOKIE_NAME, sign_session())
    return client


def test_expenses_page_requires_session(client: TestClient) -> None:
    response = client.get("/ui/expenses")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_expenses_page_shows_form_and_monthly_total(
    authenticated_ui_client: TestClient,
) -> None:
    response = authenticated_ui_client.get("/ui/expenses")

    assert response.status_code == 200
    assert 'name="amount"' in response.text
    assert "Total: USD 0.00" in response.text


def test_expense_post_parses_decimal_minor_units(
    authenticated_ui_client: TestClient,
) -> None:
    response = authenticated_ui_client.post(
        "/ui/expenses",
        data={"amount": "12.50", "currency": "usd", "category": "food", "note": "lunch"},
    )

    assert response.status_code == 200
    assert "USD 12.50" in response.text
    assert "food" in response.text
    assert "lunch" in response.text
    assert response.headers["HX-Retarget"] == "#expenses-list"
    assert response.headers["HX-Reswap"] == "afterbegin"


@pytest.mark.parametrize("amount", ["abc", "-5", "0"])
def test_expense_post_rejects_invalid_amount(
    authenticated_ui_client: TestClient,
    amount: str,
) -> None:
    response = authenticated_ui_client.post(
        "/ui/expenses",
        data={"amount": amount, "category": "invalid"},
    )

    assert response.status_code == 422
    assert "valid amount" in response.text
    listing = authenticated_ui_client.get("/ui/expenses")
    assert "invalid" not in listing.text


def test_expense_delete_soft_deletes(
    authenticated_ui_client: TestClient,
) -> None:
    created = authenticated_ui_client.post(
        "/ui/expenses",
        data={"amount": "2.00", "category": "delete-me"},
    )
    expense_id = created.text.split('id="expense-', maxsplit=1)[1].split('"', maxsplit=1)[0]

    deleted = authenticated_ui_client.delete(f"/ui/expenses/{expense_id}")
    listing = authenticated_ui_client.get("/ui/expenses")

    assert deleted.status_code == 200
    assert "delete-me" not in listing.text


def test_chart_has_proportional_bar_widths(
    authenticated_ui_client: TestClient,
) -> None:
    for category, amount in [("small", "1.00"), ("medium", "2.00"), ("large", "4.00")]:
        response = authenticated_ui_client.post(
            "/ui/expenses",
            data={"amount": amount, "category": category},
        )
        assert response.status_code == 200

    page = authenticated_ui_client.get("/ui/expenses")

    assert 'width="25.0"' in page.text
    assert 'width="50.0"' in page.text
    assert 'width="100.0"' in page.text


def test_empty_chart_message_and_xss_escaping(
    authenticated_ui_client: TestClient,
) -> None:
    empty = authenticated_ui_client.get("/ui/expenses")
    assert "No expenses this month." in empty.text

    created = authenticated_ui_client.post(
        "/ui/expenses",
        data={"amount": "1.00", "category": "<script>alert(1)</script>"},
    )
    page = authenticated_ui_client.get("/ui/expenses")

    assert created.status_code == 200
    assert "&lt;script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text
