from fastapi import Request
from fastapi.responses import JSONResponse
import structlog
from asgi_correlation_id import correlation_id
from typing import Any, Optional

logger = structlog.get_logger()

class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

async def app_error_handler(request: Request, exc: AppError):
    logger.error("app_error", message=exc.message, error_code=exc.error_code, status_code=exc.status_code)
    content = {
        "error_code": exc.error_code,
        "message": exc.message,
        "request_id": correlation_id.get(),
    }
    content.update(exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )
