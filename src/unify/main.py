from fastapi import APIRouter, Depends, FastAPI

from unify import __version__
from unify.auth import require_token
from unify.config import settings
from unify.routers import bookmarks, notes

health_router = APIRouter()
api_router = APIRouter(prefix="/api", dependencies=[Depends(require_token)])
api_router.include_router(notes.router)
api_router.include_router(bookmarks.router)


@health_router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.environment,
    }


@api_router.get("/whoami")
def whoami() -> dict[str, str]:
    return {"status": "authenticated"}


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
