import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from unify.config import settings

bearer = HTTPBearer(auto_error=False)


def require_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),  # noqa: B008
) -> None:
    if creds is None:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not secrets.compare_digest(creds.credentials, settings.api_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
