from fastapi import APIRouter, Response
from sqlalchemy import text
import structlog

from app.db.session import AsyncSessionLocal

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "TripOS API is healthy"}


@router.get("/ready")
async def readiness_check(response: Response):
    """AUDIT-020: never expose raw DB exception strings to clients."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "connected"}
    except Exception as e:
        logger.error("readiness_db_failed", error=str(e))
        response.status_code = 503
        return {"status": "not_ready", "db": "disconnected"}
