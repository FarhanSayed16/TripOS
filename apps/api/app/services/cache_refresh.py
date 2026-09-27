"""Background shopping-cache refresh for hot routes (live-inventory Phase 5)."""
from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.registry import AdapterRegistry
from app.core.circuit_breaker import circuit_breaker
from app.core.config import settings
from app.services import search_cache
from app.services.search_popularity import get_popular_routes
from app.services.supplier_usage import record_live_call
from app.services.l2b_survival import get_survival_state

logger = structlog.get_logger()


async def refresh_hot_routes(db: AsyncSession, payload: Optional[dict] = None) -> dict[str, Any]:
    """
    Refresh top-N popular search routes into Redis.
    Meters live calls as source=cache_refresh (no org_id).
    Skips suppliers with open circuit breakers.
    Phase 7: when survival pause_warm_refresh, only refresh hot band.
    """
    payload = payload or {}
    if not settings.SEARCH_CACHE_ENABLED:
        logger.info("cache_refresh_skipped", reason="SEARCH_CACHE_ENABLED=false")
        return {"skipped": True, "reason": "cache_disabled"}
    if not settings.SEARCH_CACHE_REFRESH_ENABLED:
        logger.info("cache_refresh_skipped", reason="SEARCH_CACHE_REFRESH_ENABLED=false")
        return {"skipped": True, "reason": "refresh_disabled"}

    survival = await get_survival_state(db)
    pause_warm = bool(survival.get("pause_warm_refresh"))

    top_n = int(payload.get("top_n") or settings.SEARCH_CACHE_TOP_N)
    hot_n = int(payload.get("hot_n") or settings.SEARCH_CACHE_HOT_TOP_N)
    days = int(payload.get("days") or 7)

    routes = await get_popular_routes(db, days=days, limit=top_n)
    supplier_codes = settings.inventory_supplier_codes
    refreshed = 0
    skipped_circuit = 0
    skipped_warm = 0
    errors = 0

    for rank, route in enumerate(routes):
        band = "hot" if rank < hot_n else "warm"
        if pause_warm and band == "warm":
            skipped_warm += 1
            continue
        try:
            query = route.to_search_query()
        except Exception as e:
            logger.warning("cache_refresh_bad_route", error=str(e), route=str(route))
            errors += 1
            continue

        for code in supplier_codes:
            if circuit_breaker.is_open(code):
                skipped_circuit += 1
                continue
            try:
                adapter = AdapterRegistry.get_adapter(code)
            except ValueError:
                continue

            got_lock = await search_cache.acquire_singleflight(code, query)
            if not got_lock:
                # Another refresher / user miss fill in progress
                continue
            try:
                offers = await adapter.search(query) or []
                await record_live_call(
                    db, code, "search", "cache_refresh", org_id=None
                )
                await search_cache.set_offers(code, query, offers, band=band)
                circuit_breaker.record_success(code)
                refreshed += 1
                logger.info(
                    "cache_refresh_ok",
                    supplier=code,
                    origin=route.origin,
                    destination=route.destination,
                    band=band,
                    offers=len(offers),
                    hits=route.hits,
                )
            except Exception as e:
                errors += 1
                circuit_breaker.record_failure(code)
                logger.warning(
                    "cache_refresh_failed",
                    supplier=code,
                    origin=route.origin,
                    destination=route.destination,
                    error=str(e),
                )
            finally:
                await search_cache.release_singleflight(code, query)

    try:
        await db.commit()
    except Exception as e:
        logger.warning("cache_refresh_commit_failed", error=str(e))

    result = {
        "skipped": False,
        "routes": len(routes),
        "refreshed": refreshed,
        "skipped_circuit": skipped_circuit,
        "skipped_warm": skipped_warm,
        "errors": errors,
        "top_n": top_n,
        "hot_n": hot_n,
        "survival_active": survival.get("active"),
        "pause_warm_refresh": pause_warm,
        "ttl_multiplier": survival.get("ttl_multiplier"),
    }
    logger.info("cache_refresh_done", **result)
    return result


async def handle_inventory_cache_refresh(payload: dict, db: AsyncSession) -> None:
    """Outbox handler entrypoint (type=inventory_cache_refresh)."""
    await refresh_hot_routes(db, payload or {})
