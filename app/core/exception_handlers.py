import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError

logger = logging.getLogger("app")

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(f"App error: {exc.message} (code: {exc.code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.exception("Unexpected error occurred")
        return JSONResponse(
            status_code=500,
            content={
                "message": "An unexpected error occurred",
                "code": "INTERNAL_SERVER_ERROR",
                "details": {},
            },
        )
