from fastapi import HTTPException, Request

from unify.sessions import COOKIE_NAME, load_session


def require_ui_session(request: Request) -> None:
    token = request.cookies.get(COOKIE_NAME)
    if token is not None and load_session(token):
        return
    if request.headers.get("HX-Request", "").lower() == "true":
        raise HTTPException(status_code=401, headers={"HX-Redirect": "/login"})
    raise HTTPException(status_code=303, headers={"Location": "/login"})
