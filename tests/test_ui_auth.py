from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer

from unify.config import Settings, settings
from unify.sessions import COOKIE_NAME, load_session, sign_session
from unify.ui.login import _attempts


@pytest.fixture
def auth_client(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(settings, "ui_password", "test-pw")
    monkeypatch.setattr(settings, "session_secret", "test-secret")
    _attempts.clear()
    yield client
    _attempts.clear()


def test_notes_redirects_without_cookie(auth_client: TestClient) -> None:
    response = auth_client.get("/ui/notes")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_notes_accepts_valid_signed_cookie(auth_client: TestClient) -> None:
    auth_client.cookies.set(COOKIE_NAME, sign_session())

    response = auth_client.get("/ui/notes")

    assert response.status_code == 200


def test_tampered_cookie_redirects_to_login(auth_client: TestClient) -> None:
    auth_client.cookies.set(COOKIE_NAME, "tampered")

    response = auth_client.get("/ui/notes")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_expired_cookie_redirects_to_login(
    auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    serializer = URLSafeTimedSerializer("test-secret", salt="unify-ui")
    token = serializer.dumps({"uid": "owner"})
    monkeypatch.setattr("unify.ui.auth.load_session", lambda value: load_session(value, max_age=-1))
    auth_client.cookies.set(COOKIE_NAME, token)

    response = auth_client.get("/ui/notes")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_htmx_request_gets_hx_redirect(auth_client: TestClient) -> None:
    response = auth_client.get("/ui/notes", headers={"HX-Request": "true"})

    assert response.status_code == 401
    assert response.headers["hx-redirect"] == "/login"


def test_login_success_sets_secure_session_cookie(auth_client: TestClient) -> None:
    response = auth_client.post("/login", data={"password": "test-pw"})

    assert response.status_code == 303
    assert response.headers["location"] == "/ui/notes"
    cookie = response.headers["set-cookie"]
    assert "unify_session=" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()


def test_login_failure_does_not_set_cookie(auth_client: TestClient) -> None:
    response = auth_client.post("/login", data={"password": "wrong"})

    assert response.status_code == 401
    assert "Invalid password" in response.text
    assert "set-cookie" not in response.headers


def test_sixth_login_attempt_is_rate_limited(auth_client: TestClient) -> None:
    responses = [auth_client.post("/login", data={"password": "wrong"}) for _ in range(6)]

    assert [response.status_code for response in responses] == [401, 401, 401, 401, 401, 429]


def test_logout_redirects_and_clears_cookie(auth_client: TestClient) -> None:
    auth_client.cookies.set(COOKIE_NAME, sign_session())

    response = auth_client.post("/logout")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    cookie = response.headers["set-cookie"].lower()
    assert "unify_session" in cookie
    assert "max-age=0" in cookie or "expires=" in cookie


def test_public_landing_and_protected_api(auth_client: TestClient) -> None:
    assert auth_client.get("/").status_code == 200
    assert auth_client.get("/api/notes").status_code == 401


def test_production_rejects_default_ui_password_or_secret() -> None:
    with pytest.raises(ValueError, match="default UI credentials"):
        Settings(
            environment="prod",
            api_token="custom-api-token",
            ui_password="dev-password-change-me",
            session_secret="custom-session-secret",
        )
    with pytest.raises(ValueError, match="default UI credentials"):
        Settings(
            environment="prod",
            api_token="custom-api-token",
            ui_password="custom-ui-password",
            session_secret="dev-session-secret-change-me",
        )


def test_login_form_is_rendered(auth_client: TestClient) -> None:
    response = auth_client.get("/login")

    assert response.status_code == 200
    assert 'name="password"' in response.text
