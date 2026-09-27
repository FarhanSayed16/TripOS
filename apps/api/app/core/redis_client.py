"""Async Redis helpers for shopping cache (live-inventory Phase 2)."""
from __future__ import annotations

from typing import Any, Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()

_client = None


def get_redis():
    """Lazy singleton redis.asyncio client (decode_responses=True)."""
    global _client
    if _client is None:
        import redis.asyncio as redis

        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
        _client = None


async def get_json(key: str) -> Optional[dict[str, Any]]:
    try:
        import json

        raw = await get_redis().get(key)
        if raw is None:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception as e:
        logger.warning("redis_get_json_failed", key=key, error=str(e))
        return None


async def set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> bool:
    try:
        import json

        await get_redis().set(key, json.dumps(value), ex=max(1, int(ttl_seconds)))
        return True
    except Exception as e:
        logger.warning("redis_set_json_failed", key=key, error=str(e))
        return False


async def try_lock(key: str, ttl_seconds: int = 5) -> bool:
    """
    SET NX EX — True if this caller holds the lock.
    On Redis errors, return True (fail open → allow live search).
    """
    try:
        ok = await get_redis().set(key, "1", nx=True, ex=max(1, int(ttl_seconds)))
        return bool(ok)
    except Exception as e:
        logger.warning("redis_try_lock_failed", key=key, error=str(e))
        return True


async def release_lock(key: str) -> None:
    try:
        await get_redis().delete(key)
    except Exception as e:
        logger.warning("redis_release_lock_failed", key=key, error=str(e))
