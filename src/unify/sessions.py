from itsdangerous import URLSafeTimedSerializer

from unify.config import settings

COOKIE_NAME = "unify_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="unify-ui")


def sign_session() -> str:
    return _serializer().dumps({"uid": "owner"})


def load_session(token: str, *, max_age: int = SESSION_MAX_AGE) -> bool:
    try:
        payload: object = _serializer().loads(token, max_age=max_age)
    except Exception:
        return False
    return payload == {"uid": "owner"}
