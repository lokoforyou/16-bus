from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
