from fastapi import APIRouter, Depends, FastAPI, Request, Response

from unify import __version__
from unify.auth import require_token
from unify.config import settings
from unify.routers import bookmarks, notes
from unify.ui import bookmarks as bookmarks_ui
from unify.ui import login as login_ui
from unify.ui import notes as notes_ui
from unify.ui.templating import templates

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


def landing_page(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="index.html", context={})


@api_router.get("/whoami")
def whoami() -> dict[str, str]:
    return {"status": "authenticated"}


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(health_router)
    app.include_router(api_router)
    if settings.environment == "dev":
        app.add_api_route("/", landing_page, methods=["GET"], tags=["ui"])
        app.include_router(login_ui.router)
        app.include_router(notes_ui.router)
        app.include_router(bookmarks_ui.router)
    return app


app = create_app()
