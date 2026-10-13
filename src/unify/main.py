from fastapi import APIRouter, FastAPI

from unify import __version__
from unify.config import settings

health_router = APIRouter()


@health_router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.environment,
    }


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__)
    app.include_router(health_router)
    return app


app = create_app()
