import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.commercial import Payment

logger = structlog.get_logger()


async def claim_idempotency_key(db: AsyncSession, key: str, action: str) -> bool:
    """
    Returns True if this key is free to use (caller should proceed).
    Returns False if a Payment row already owns this idempotency_key.
    DB unique constraint remains the final race guard.
    """
    logger.info("check_idempotency", key=key, action=action)
    existing = (
        await db.execute(select(Payment).where(Payment.idempotency_key == key))
    ).scalar_one_or_none()
    return existing is None
