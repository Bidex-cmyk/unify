import secrets
import time

from fastapi import APIRouter, Form, Request, Response
from starlette.responses import RedirectResponse

from unify.config import settings
from unify.sessions import COOKIE_NAME, SESSION_MAX_AGE, load_session, sign_session
from unify.ui.templating import templates

router = APIRouter(tags=["ui-auth"])
_attempts: dict[str, list[float]] = {}


def _too_many_attempts(client_ip: str, now: float) -> bool:
    attempts = [timestamp for timestamp in _attempts.get(client_ip, []) if now - timestamp < 60]
    if len(attempts) >= 5:
        _attempts[client_ip] = attempts
        return True
    attempts.append(now)
    _attempts[client_ip] = attempts
    return False


@router.get("/login")
def login_page(request: Request) -> Response:
    if load_session(request.cookies.get(COOKIE_NAME, "")):
        return RedirectResponse("/ui/notes", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@router.post("/login")
def login(
    request: Request,
    password: str = Form(""),
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    if _too_many_attempts(client_ip, time.monotonic()):
        return Response(status_code=429, content="Too many login attempts")
    if not secrets.compare_digest(password.encode(), settings.ui_password.encode()):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid password"},
            status_code=401,
        )
    response = RedirectResponse("/ui/notes", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        sign_session(),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.environment != "dev",
        path="/",
    )
    return response


@router.post("/logout")
def logout() -> Response:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
