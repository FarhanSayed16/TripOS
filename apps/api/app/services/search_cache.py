"""Shopping search cache — one live search per route/supplier within TTL."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import structlog

from app.core import redis_client
from app.core.config import settings
from app.schemas.inventory import NormalizedOffer, SearchQuery
from app.services.l2b_survival import effective_cache_ttl

logger = structlog.get_logger()


@dataclass
class CacheHit:
    offers: List[NormalizedOffer]
    fetched_at: datetime
    ttl_seconds: int
    age_seconds: int


def cache_key(supplier_code: str, query: SearchQuery) -> str:
    inv_type = query.type.value if hasattr(query.type, "value") else str(query.type)
    ret = query.return_date.isoformat() if query.return_date else "-"
    pax = query.passengers
    deal = (query.deal_code or "").strip().upper() or "-"
    if deal == "-" and query.deal_codes:
        deal = ",".join(sorted(str(c).strip().upper() for c in query.deal_codes if c)) or "-"
    return (
        f"inv:{supplier_code}:{inv_type}:"
        f"{query.origin.upper()}:{query.destination.upper()}:"
        f"{query.departure_date.isoformat()}:{ret}:"
        f"{pax.adults}:{pax.children}:{pax.infants}:deal:{deal}"
    )


def lock_key(supplier_code: str, query: SearchQuery) -> str:
    return f"{cache_key(supplier_code, query)}:lock"


async def get_offers(supplier_code: str, query: SearchQuery) -> Optional[CacheHit]:
    if not settings.SEARCH_CACHE_ENABLED:
        return None
    key = cache_key(supplier_code, query)
    data = await redis_client.get_json(key)
    if not data:
        return None
    try:
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        ttl = int(data.get("ttl_seconds") or settings.SEARCH_CACHE_TTL_SECONDS)
        age = max(0, int((datetime.now(timezone.utc) - fetched_at).total_seconds()))
        offers = [NormalizedOffer.model_validate(o) for o in data.get("offers") or []]
        logger.info(
            "search_cache_hit",
            supplier=supplier_code,
            key=key,
            age_seconds=age,
            offers=len(offers),
        )
        return CacheHit(offers=offers, fetched_at=fetched_at, ttl_seconds=ttl, age_seconds=age)
    except Exception as e:
        logger.warning("search_cache_decode_failed", key=key, error=str(e))
        return None


async def set_offers(
    supplier_code: str,
    query: SearchQuery,
    offers: List[NormalizedOffer],
    *,
    ttl_seconds: Optional[int] = None,
    band: str = "default",
) -> None:
    if not settings.SEARCH_CACHE_ENABLED:
        return
    key = cache_key(supplier_code, query)
    if ttl_seconds is not None:
        ttl = max(1, int(ttl_seconds))
    elif band == "hot":
        ttl = max(1, int(settings.SEARCH_CACHE_HOT_TTL_SECONDS))
    elif band == "warm":
        ttl = max(1, int(settings.SEARCH_CACHE_WARM_TTL_SECONDS))
    else:
        ttl = max(1, int(settings.SEARCH_CACHE_TTL_SECONDS))
    # Phase 7: widen TTL when platform L2B survival is active
    base_ttl = ttl
    ttl = effective_cache_ttl(ttl)
    payload = {
        "offers": [o.model_dump(mode="json") for o in offers],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "ttl_seconds": ttl,
        "band": band,
        "ttl_base_seconds": base_ttl,
    }
    ok = await redis_client.set_json(key, payload, ttl)
    if ok:
        logger.info(
            "search_cache_set",
            supplier=supplier_code,
            key=key,
            ttl=ttl,
            ttl_base=base_ttl,
            band=band,
            offers=len(offers),
        )


async def acquire_singleflight(supplier_code: str, query: SearchQuery) -> bool:
    """Return True if caller should run live search (holds lock or Redis fail-open)."""
    if not settings.SEARCH_CACHE_ENABLED:
        return True
    return await redis_client.try_lock(lock_key(supplier_code, query), ttl_seconds=5)


async def release_singleflight(supplier_code: str, query: SearchQuery) -> None:
    if not settings.SEARCH_CACHE_ENABLED:
        return
    await redis_client.release_lock(lock_key(supplier_code, query))
