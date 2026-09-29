import time
import uuid
from typing import Dict, List, Optional
from fastapi import HTTPException
import structlog

logger = structlog.get_logger()

class RateLimiter:
    """
    A simple in-memory token bucket / sliding window rate limiter for pilot phase.
    Tracks requests per organization.
    """
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        # Dict[org_id, List[timestamp]]
        self._history: Dict[uuid.UUID, List[float]] = {}
        
    def check_rate_limit(self, org_id: uuid.UUID):
        now = time.time()
        window_start = now - 60.0
        
        # Clean old timestamps
        history = self._history.get(org_id, [])
        history = [ts for ts in history if ts > window_start]
        
        if len(history) >= self.requests_per_minute:
            logger.warning("rate_limit_exceeded", org_id=str(org_id), count=len(history))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 30 searches per minute."
            )
            
        history.append(now)
        self._history[org_id] = history

        # ISSUE-01: Prune stale org entries to prevent memory leak
        if len(self._history) > 100:
            self._history = {
                k: [ts for ts in v if ts > window_start]
                for k, v in self._history.items()
                if any(ts > window_start for ts in v)
            }


# Global instance
inventory_rate_limiter = RateLimiter(requests_per_minute=30)


class PartnerRateLimiter:
    """
    Per-partner-app sliding window (FC Phase 8).
    Prefers Redis so multi-worker deployments share the budget; falls back to memory.
    """

    def __init__(self):
        self._history: Dict[uuid.UUID, List[float]] = {}

    def _memory_check(self, partner_app_id: uuid.UUID, limit: int):
        now = time.time()
        window_start = now - 60.0
        history = self._history.get(partner_app_id, [])
        history = [ts for ts in history if ts > window_start]
        if len(history) >= limit:
            logger.warning(
                "partner_rate_limit_exceeded",
                partner_app_id=str(partner_app_id),
                count=len(history),
                limit=limit,
                backend="memory",
            )
            raise HTTPException(
                status_code=429,
                detail=f"Partner rate limit exceeded. Maximum {limit} requests per minute.",
            )
        history.append(now)
        self._history[partner_app_id] = history
        if len(self._history) > 200:
            self._history = {
                k: [ts for ts in v if ts > window_start]
                for k, v in self._history.items()
                if any(ts > window_start for ts in v)
            }

    async def check(self, partner_app_id: uuid.UUID, limit_per_minute: int):
        limit = max(1, int(limit_per_minute or 60))
        key = f"partner:rl:{partner_app_id}"
        try:
            from app.core import redis_client

            r = redis_client.get_redis()
            # Sliding window via sorted set of timestamps
            now = time.time()
            window_start = now - 60.0
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
            pipe.expire(key, 120)
            results = await pipe.execute()
            count_before = int(results[1] or 0)
            if count_before >= limit:
                # Undo the add we just made
                await r.zremrangebyscore(key, now - 0.001, now + 0.001)
                logger.warning(
                    "partner_rate_limit_exceeded",
                    partner_app_id=str(partner_app_id),
                    count=count_before,
                    limit=limit,
                    backend="redis",
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Partner rate limit exceeded. Maximum {limit} requests per minute.",
                )
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(
                "partner_rate_limit_redis_fallback",
                error=str(e),
                partner_app_id=str(partner_app_id),
            )
            self._memory_check(partner_app_id, limit)


partner_rate_limiter = PartnerRateLimiter()


def client_ip_from_request(request) -> Optional[str]:
    """
    Best-effort client IP. Prefer first X-Forwarded-For hop when present
    (expects a trusted reverse proxy to set/overwrite the header).
    """
    if request is None:
        return None
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip") or request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return None
