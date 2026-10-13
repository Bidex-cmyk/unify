import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from unify.config import Settings, settings
from unify.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "api_token", "test-token")
    return TestClient(app)


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_whoami_requires_token(client: TestClient) -> None:
    response = client.get("/api/whoami")

    assert response.status_code == 401


def test_whoami_rejects_wrong_token(client: TestClient) -> None:
    response = client.get("/api/whoami", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401


def test_whoami_rejects_malformed_authorization(client: TestClient) -> None:
    response = client.get("/api/whoami", headers={"Authorization": "Token abc"})

    assert response.status_code == 401


def test_whoami_accepts_correct_token(client: TestClient) -> None:
    response = client.get("/api/whoami", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"status": "authenticated"}


def test_settings_reject_default_token_outside_dev() -> None:
    with pytest.raises(ValidationError, match="refusing to start in non-dev with default token"):
        Settings(environment="prod", api_token="dev-token-change-me")
