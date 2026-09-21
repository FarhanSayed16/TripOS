import time
import uuid
from typing import Dict, List
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
