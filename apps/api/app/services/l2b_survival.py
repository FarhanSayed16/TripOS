"""Platform L2B survival soft-brakes (live-inventory Phase 7)."""
from __future__ import annotations

import time
from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.supplier_usage import summarize_l2b

logger = structlog.get_logger()

# In-process cache so set_offers can widen TTL without a DB round-trip every write.
_cached: Optional[tuple[float, dict[str, Any]]] = None
_CACHE_SECONDS = 45.0
_last_sentry_at = 0.0
_SENTRY_COOLDOWN_SECONDS = 300.0


def _default_state() -> dict[str, Any]:
    return {
        "enabled": bool(settings.L2B_SURVIVAL_ENABLED),
        "active": False,
        "status": "ok",
        "l2b_ratio": 0.0,
        "looks": 0,
        "confirmed_bookings": 0,
        "ttl_multiplier": 1.0,
        "ttl_cap_seconds": int(settings.L2B_SURVIVAL_TTL_CAP_SECONDS),
        "pause_warm_refresh": False,
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
    }


def peek_survival() -> dict[str, Any]:
    """Sync snapshot for cache TTL helpers (may be stale up to ~45s)."""
    if _cached is None:
        return _default_state()
    return dict(_cached[1])


def effective_cache_ttl(base_ttl_seconds: int) -> int:
    """Widen TTL when survival is active; never exceed cap."""
    base = max(1, int(base_ttl_seconds))
    state = peek_survival()
    if not state.get("enabled") or not state.get("active"):
        return base
    mult = float(state.get("ttl_multiplier") or 1.0)
    cap = max(base, int(state.get("ttl_cap_seconds") or settings.L2B_SURVIVAL_TTL_CAP_SECONDS))
    widened = int(base * mult)
    return max(1, min(widened, cap))


def _maybe_sentry_alert(state: dict[str, Any]) -> None:
    global _last_sentry_at
    if not state.get("active"):
        return
    now = time.monotonic()
    if now - _last_sentry_at < _SENTRY_COOLDOWN_SECONDS:
        return
    _last_sentry_at = now
    logger.error(
        "l2b_survival_critical",
        l2b_ratio=state.get("l2b_ratio"),
        looks=state.get("looks"),
        confirmed_bookings=state.get("confirmed_bookings"),
        ttl_multiplier=state.get("ttl_multiplier"),
        pause_warm_refresh=state.get("pause_warm_refresh"),
    )
    try:
        if settings.SENTRY_DSN:
            import sentry_sdk

            sentry_sdk.capture_message(
                (
                    f"L2B survival ACTIVE: ratio={state.get('l2b_ratio')} "
                    f"(looks={state.get('looks')}, confirmed={state.get('confirmed_bookings')})"
                ),
                level="error",
            )
    except Exception as e:
        logger.warning("l2b_survival_sentry_failed", error=str(e))


async def get_survival_state(
    db: AsyncSession,
    *,
    force: bool = False,
    days: int = 7,
) -> dict[str, Any]:
    """
    Evaluate platform L2B and derive soft-brake actions.
    Updates in-process cache used by effective_cache_ttl().
    """
    global _cached

    if not settings.L2B_SURVIVAL_ENABLED:
        state = _default_state()
        state["enabled"] = False
        _cached = (time.monotonic(), state)
        return state

    now = time.monotonic()
    if not force and _cached is not None and (now - _cached[0]) < _CACHE_SECONDS:
        return dict(_cached[1])

    summary = await summarize_l2b(db, days=days)
    critical = summary.get("status") == "critical"
    mult = float(settings.L2B_SURVIVAL_TTL_MULTIPLIER) if critical else 1.0
    pause_warm = bool(critical and settings.L2B_SURVIVAL_PAUSE_WARM_REFRESH)

    state = {
        "enabled": True,
        "active": critical,
        "status": summary.get("status"),
        "l2b_ratio": summary.get("l2b_ratio"),
        "looks": summary.get("looks"),
        "confirmed_bookings": summary.get("confirmed_bookings"),
        "ttl_multiplier": mult,
        "ttl_cap_seconds": int(settings.L2B_SURVIVAL_TTL_CAP_SECONDS),
        "pause_warm_refresh": pause_warm,
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
        "window_days": summary.get("window_days", days),
    }
    _cached = (now, state)

    if critical:
        logger.warning(
            "l2b_survival_active",
            l2b_ratio=state["l2b_ratio"],
            ttl_multiplier=mult,
            ttl_cap_seconds=state["ttl_cap_seconds"],
            pause_warm_refresh=pause_warm,
        )
        _maybe_sentry_alert(state)
    else:
        logger.info(
            "l2b_survival_idle",
            status=state["status"],
            l2b_ratio=state["l2b_ratio"],
        )

    return dict(state)


def reset_survival_cache_for_tests() -> None:
    """Test helper — clear in-process survival cache + sentry cooldown."""
    global _cached, _last_sentry_at
    _cached = None
    _last_sentry_at = 0.0
