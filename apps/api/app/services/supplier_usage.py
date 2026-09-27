"""Live supplier call metering + L2B rollups (Phases 1 + 4)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.inventory import SupplierUsageDaily, SupplierUsageDailyOrg

logger = structlog.get_logger()

UsageKind = Literal["search", "revalidate", "book", "confirmed"]
LiveSearchPolicy = Literal["allow", "cache_only", "block"]

_KIND_COLUMN = {
    "search": "searches",
    "revalidate": "revalidates",
    "book": "books",
    "confirmed": "confirmed_bookings",
}


def compute_l2b_ratio(searches: int, revalidates: int, confirmed_bookings: int) -> float:
    """Looks = searches + revalidates; divide by confirmed (floor 1)."""
    looks = max(0, int(searches)) + max(0, int(revalidates))
    return looks / max(int(confirmed_bookings), 1)


def l2b_status(ratio: float) -> str:
    if ratio >= settings.L2B_CRITICAL_RATIO:
        return "critical"
    if ratio >= settings.L2B_WARN_RATIO:
        return "warn"
    return "ok"


def _as_uuid(org_id: Any) -> Optional[UUID]:
    if org_id is None:
        return None
    if isinstance(org_id, UUID):
        return org_id
    try:
        return UUID(str(org_id))
    except (ValueError, TypeError):
        return None


async def record_live_call(
    db: AsyncSession,
    supplier_code: str,
    kind: UsageKind,
    source: str,
    org_id: Optional[Any] = None,
) -> None:
    """
    Upsert today's platform + per-org daily rollups.
    Failures are swallowed so metering never breaks search/pay/book.
    """
    if not supplier_code or kind not in _KIND_COLUMN:
        return
    col = _KIND_COLUMN[kind]
    today = datetime.now(timezone.utc).date()
    try:
        values = {
            "day": today,
            "supplier_code": supplier_code,
            "searches": 0,
            "revalidates": 0,
            "books": 0,
            "confirmed_bookings": 0,
            col: 1,
        }
        stmt = insert(SupplierUsageDaily).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["day", "supplier_code"],
            set_={col: getattr(SupplierUsageDaily, col) + 1},
        )
        await db.execute(stmt)

        org_uuid = _as_uuid(org_id)
        if org_uuid is not None:
            org_values = {
                "day": today,
                "organization_id": org_uuid,
                "supplier_code": supplier_code,
                "searches": 0,
                "revalidates": 0,
                "books": 0,
                "confirmed_bookings": 0,
                col: 1,
            }
            org_stmt = insert(SupplierUsageDailyOrg).values(**org_values)
            org_stmt = org_stmt.on_conflict_do_update(
                index_elements=["day", "organization_id", "supplier_code"],
                set_={col: getattr(SupplierUsageDailyOrg, col) + 1},
            )
            await db.execute(org_stmt)

        await db.flush()
        logger.info(
            "supplier_usage_recorded",
            supplier_code=supplier_code,
            kind=kind,
            source=source,
            org_id=str(org_uuid) if org_uuid else None,
            day=str(today),
        )
    except Exception as e:
        logger.warning(
            "supplier_usage_record_failed",
            supplier_code=supplier_code,
            kind=kind,
            source=source,
            error=str(e),
        )


def _rollup_rows(rows) -> dict:
    totals = {
        "searches": 0,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 0,
    }
    for row in rows:
        totals["searches"] += row.searches
        totals["revalidates"] += row.revalidates
        totals["books"] += row.books
        totals["confirmed_bookings"] += row.confirmed_bookings
    looks = totals["searches"] + totals["revalidates"]
    ratio = compute_l2b_ratio(
        totals["searches"], totals["revalidates"], totals["confirmed_bookings"]
    )
    return {
        **totals,
        "looks": looks,
        "l2b_ratio": round(ratio, 2),
        "status": l2b_status(ratio),
    }


async def summarize_l2b(db: AsyncSession, days: int = 7) -> dict:
    """Platform + per-supplier L2B for the last `days` calendar days (UTC)."""
    days = max(1, min(int(days), 90))
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    rows = (
        await db.execute(
            select(SupplierUsageDaily).where(
                SupplierUsageDaily.day >= start,
                SupplierUsageDaily.day <= end,
            )
        )
    ).scalars().all()

    by_supplier: dict[str, dict] = {}
    totals = {
        "searches": 0,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 0,
    }
    for row in rows:
        totals["searches"] += row.searches
        totals["revalidates"] += row.revalidates
        totals["books"] += row.books
        totals["confirmed_bookings"] += row.confirmed_bookings
        bucket = by_supplier.setdefault(
            row.supplier_code,
            {
                "supplier_code": row.supplier_code,
                "searches": 0,
                "revalidates": 0,
                "books": 0,
                "confirmed_bookings": 0,
            },
        )
        bucket["searches"] += row.searches
        bucket["revalidates"] += row.revalidates
        bucket["books"] += row.books
        bucket["confirmed_bookings"] += row.confirmed_bookings

    looks = totals["searches"] + totals["revalidates"]
    ratio = compute_l2b_ratio(
        totals["searches"], totals["revalidates"], totals["confirmed_bookings"]
    )
    suppliers_out = []
    for code, b in sorted(by_supplier.items()):
        r = compute_l2b_ratio(b["searches"], b["revalidates"], b["confirmed_bookings"])
        suppliers_out.append(
            {
                **b,
                "looks": b["searches"] + b["revalidates"],
                "l2b_ratio": round(r, 2),
                "status": l2b_status(r),
            }
        )

    return {
        "window_days": days,
        "start_day": str(start),
        "end_day": str(end),
        "searches": totals["searches"],
        "revalidates": totals["revalidates"],
        "books": totals["books"],
        "confirmed_bookings": totals["confirmed_bookings"],
        "looks": looks,
        "l2b_ratio": round(ratio, 2),
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
        "status": l2b_status(ratio),
        "by_supplier": suppliers_out,
    }


async def summarize_org_l2b(db: AsyncSession, org_id: Any, days: int = 7) -> dict:
    """Aggregate L2B for one organization across suppliers."""
    days = max(1, min(int(days), 90))
    org_uuid = _as_uuid(org_id)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    empty = {
        "organization_id": str(org_id) if org_id else None,
        "window_days": days,
        "start_day": str(start),
        "end_day": str(end),
        "searches": 0,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 0,
        "looks": 0,
        "l2b_ratio": 0.0,
        "status": "ok",
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
    }
    if org_uuid is None:
        return empty

    rows = (
        await db.execute(
            select(SupplierUsageDailyOrg).where(
                SupplierUsageDailyOrg.organization_id == org_uuid,
                SupplierUsageDailyOrg.day >= start,
                SupplierUsageDailyOrg.day <= end,
            )
        )
    ).scalars().all()
    rolled = _rollup_rows(rows)
    return {
        "organization_id": str(org_uuid),
        "window_days": days,
        "start_day": str(start),
        "end_day": str(end),
        **rolled,
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
    }


async def get_org_live_search_policy(
    db: AsyncSession,
    org_id: Any,
    *,
    usage_source: str = "user_search",
) -> tuple[LiveSearchPolicy, dict]:
    """
    Decide whether this org may fire a live supplier search.
    - block: critical L2B with too few confirmed bookings
    - cache_only: warn/critical when L2B_ORG_CACHE_ONLY
    - allow: otherwise
    """
    summary = await summarize_org_l2b(db, org_id, days=7)
    status = summary["status"]
    confirmed = int(summary["confirmed_bookings"])
    min_confirmed = max(0, int(settings.L2B_THROTTLE_MIN_CONFIRMED))

    if status == "critical" and confirmed < min_confirmed:
        return "block", summary

    if settings.L2B_ORG_CACHE_ONLY and status in ("warn", "critical"):
        return "cache_only", summary

    # AI: block live when org OR platform L2B is critical
    if usage_source == "ai_search" and settings.L2B_AI_BLOCK_ON_CRITICAL:
        if status == "critical":
            return "block", summary
        platform = await summarize_l2b(db, days=7)
        if platform["status"] == "critical":
            merged = {
                **summary,
                "platform_status": "critical",
                "platform_l2b_ratio": platform["l2b_ratio"],
            }
            return "block", merged

    return "allow", summary


async def assert_may_live_search(
    db: AsyncSession,
    org_id: Any,
    *,
    usage_source: str = "user_search",
) -> LiveSearchPolicy:
    """Raise 429 when blocked; return cache_only/allow otherwise."""
    policy, summary = await get_org_live_search_policy(
        db, org_id, usage_source=usage_source
    )
    if policy == "block":
        code = (
            "AI_SEARCH_THROTTLED_L2B"
            if usage_source == "ai_search"
            else "SEARCH_THROTTLED_L2B"
        )
        msg = (
            "AI search is paused while look-to-book is critical. Refine your query or try again later."
            if usage_source == "ai_search"
            else (
                "Live search temporarily limited for your organization due to high "
                "look-to-book ratio. Complete bookings or try again later."
            )
        )
        raise AppError(
            msg,
            status_code=429,
            error_code=code,
            details={
                "l2b_ratio": summary["l2b_ratio"],
                "confirmed_bookings_7d": summary["confirmed_bookings"],
                "looks_7d": summary["looks"],
                "status": summary["status"],
            },
        )
    return policy


async def list_org_l2b_offenders(db: AsyncSession, days: int = 7, limit: int = 20) -> list[dict]:
    """Top orgs by L2B ratio (then looks) for admin."""
    days = max(1, min(int(days), 90))
    limit = max(1, min(int(limit), 100))
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    rows = (
        await db.execute(
            select(SupplierUsageDailyOrg).where(
                SupplierUsageDailyOrg.day >= start,
                SupplierUsageDailyOrg.day <= end,
            )
        )
    ).scalars().all()

    by_org: dict[str, dict] = {}
    for row in rows:
        oid = str(row.organization_id)
        bucket = by_org.setdefault(
            oid,
            {
                "organization_id": oid,
                "searches": 0,
                "revalidates": 0,
                "books": 0,
                "confirmed_bookings": 0,
            },
        )
        bucket["searches"] += row.searches
        bucket["revalidates"] += row.revalidates
        bucket["books"] += row.books
        bucket["confirmed_bookings"] += row.confirmed_bookings

    out = []
    for oid, b in by_org.items():
        r = compute_l2b_ratio(b["searches"], b["revalidates"], b["confirmed_bookings"])
        out.append(
            {
                **b,
                "looks": b["searches"] + b["revalidates"],
                "l2b_ratio": round(r, 2),
                "status": l2b_status(r),
            }
        )
    out.sort(key=lambda x: (x["l2b_ratio"], x["looks"]), reverse=True)
    return out[:limit]
