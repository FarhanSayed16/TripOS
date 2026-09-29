import asyncio
import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.schemas.inventory import (
    SearchQuery,
    NormalizedOffer,
    SearchResponse,
    RevalidateRequest,
)
from app.models.inventory import SearchRequest
from app.models.tenancy import User
from app.adapters.registry import AdapterRegistry
from app.core.inventory_errors import InventoryRevalidateError
from app.core.exceptions import AppError
from app.core.config import settings
from app.services.supplier_usage import record_live_call, get_org_live_search_policy
from app.services import search_cache
from app.services.l2b_survival import get_survival_state

logger = structlog.get_logger()


from app.services.supplier_strategy import SupplierStrategy
from app.core.circuit_breaker import circuit_breaker


async def _apply_org_search_enrichment(
    query: SearchQuery,
    org_id,
    db: AsyncSession,
    *,
    usage_source: str,
) -> SearchQuery:
    """FC Phase 7 — org deal codes + opt-in AI preference filters."""
    if not org_id:
        return query
    from app.models.tenancy import Organization

    org = await db.get(Organization, org_id)
    if not org:
        return query

    updates: dict = {}
    org_codes = list(org.deal_codes or []) if isinstance(org.deal_codes, list) else []
    if query.deal_code:
        updates["deal_codes"] = [query.deal_code] + [c for c in org_codes if c != query.deal_code]
    elif org_codes and not query.deal_codes:
        updates["deal_codes"] = org_codes
        updates["deal_code"] = str(org_codes[0])

    prefs = org.ai_preferences if isinstance(org.ai_preferences, dict) else None
    if (
        settings.FC_AI_PREFERENCES_ENABLED
        and prefs
        and prefs.get("enabled")
        and usage_source == "ai_search"
    ):
        if query.max_stops is None and prefs.get("max_stops") is not None:
            try:
                updates["max_stops"] = int(prefs["max_stops"])
            except (TypeError, ValueError):
                pass
        if not query.airlines and prefs.get("preferred_airlines"):
            airlines = prefs["preferred_airlines"]
            if isinstance(airlines, list):
                updates["airlines"] = [str(a).upper() for a in airlines if a]

    if not updates:
        return query
    return query.model_copy(update=updates)


async def search_inventory(
    query: SearchQuery,
    current_user: User,
    db: AsyncSession,
    usage_source: str = "user_search",
) -> SearchResponse:
    """
    Orchestrates search across configured suppliers using the SupplierStrategy.
    - all: parallel fan-out (asyncio.gather)
    - primary_only: only first configured supplier
    - failover: sequential; stop after first supplier that returns offers
    When SEARCH_CACHE_ENABLED, browse hits Redis first (no L2B meter on hit).
    Phase 4: per-org L2B may block or cache-only live fills (cache hits still OK).
    """
    strategy = SupplierStrategy()
    mode = strategy.get_strategy()
    active_supplier_codes = await strategy.select_for_search(query)
    logger.info("inventory_search_suppliers", suppliers=active_supplier_codes, strategy=mode)
    org_id = current_user.active_organization_id

    # FC Phase 7 — merge org deal codes + optional AI preferences
    query = await _apply_org_search_enrichment(query, org_id, db, usage_source=usage_source)

    live_policy, l2b_summary = await get_org_live_search_policy(
        db, org_id, usage_source=usage_source
    )
    # Refresh Phase 7 survival snapshot for TTL widening on cache writes
    try:
        await get_survival_state(db)
    except Exception as e:
        logger.warning("l2b_survival_refresh_failed", error=str(e))

    cache_ages: List[int] = []
    any_cache_hit = False

    def _raise_throttled():
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
                "l2b_ratio": l2b_summary.get("l2b_ratio"),
                "confirmed_bookings_7d": l2b_summary.get("confirmed_bookings"),
                "looks_7d": l2b_summary.get("looks"),
                "status": l2b_summary.get("status"),
            },
        )

    async def _live_search_metered(adapter, q) -> List[NormalizedOffer]:
        """Live adapter call + L2B meter (only when policy allows)."""
        if live_policy == "block":
            _raise_throttled()
        if live_policy == "cache_only":
            return []
        start_time = time.time()
        try:
            res = await adapter.search(q)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "supplier_search_success",
                supplier=adapter.supplier_code,
                duration_ms=duration_ms,
            )
            try:
                from app.services.supplier_metrics import supplier_metrics

                supplier_metrics.record(adapter.supplier_code, duration_ms, ok=True)
            except Exception:
                pass
            return res
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "supplier_search_error",
                supplier=adapter.supplier_code,
                duration_ms=duration_ms,
                error=str(e),
            )
            try:
                from app.services.supplier_metrics import supplier_metrics

                supplier_metrics.record(adapter.supplier_code, duration_ms, ok=False)
            except Exception:
                pass
            raise e
        finally:
            await record_live_call(
                db,
                adapter.supplier_code,
                "search",
                usage_source,
                org_id=org_id,
            )

    async def _search_supplier(code: str, adapter) -> List[NormalizedOffer]:
        """Cache → singleflight → live; meters only live adapter.search."""
        nonlocal any_cache_hit

        if settings.SEARCH_CACHE_ENABLED:
            hit = await search_cache.get_offers(code, query)
            if hit is not None:
                any_cache_hit = True
                cache_ages.append(hit.age_seconds)
                return hit.offers

            if live_policy == "cache_only":
                logger.info(
                    "search_cache_only_skip_live",
                    supplier=code,
                    org_id=str(org_id) if org_id else None,
                    usage_source=usage_source,
                )
                return []

            if live_policy == "block":
                _raise_throttled()

            got_lock = await search_cache.acquire_singleflight(code, query)
            if not got_lock:
                await asyncio.sleep(0.25)
                hit = await search_cache.get_offers(code, query)
                if hit is not None:
                    any_cache_hit = True
                    cache_ages.append(hit.age_seconds)
                    return hit.offers
                if live_policy == "block":
                    _raise_throttled()
                if live_policy == "cache_only":
                    return []

            try:
                offers = await _live_search_metered(adapter, query)
                await search_cache.set_offers(code, query, offers or [])
                return offers or []
            finally:
                if got_lock:
                    await search_cache.release_singleflight(code, query)

        if live_policy == "cache_only":
            logger.info(
                "search_cache_only_no_cache_backend",
                supplier=code,
                org_id=str(org_id) if org_id else None,
            )
            return []
        if live_policy == "block":
            _raise_throttled()

        return await _live_search_metered(adapter, query) or []

    def _adapters_for(codes: list[str]):
        out = []
        for code in codes:
            if circuit_breaker.is_open(code):
                logger.warning("circuit_breaker_skipping_supplier", supplier=code)
                continue
            try:
                out.append((code, AdapterRegistry.get_adapter(code)))
            except ValueError as e:
                logger.error("adapter_resolution_failed", error=str(e), supplier_code=code)
        return out

    all_offers: List[NormalizedOffer] = []
    runnable = _adapters_for(active_supplier_codes)

    def _is_throttle_error(exc: BaseException) -> bool:
        return isinstance(exc, AppError) and exc.error_code in (
            "SEARCH_THROTTLED_L2B",
            "AI_SEARCH_THROTTLED_L2B",
        )

    if mode == "failover":
        for code, adapter in runnable:
            try:
                res = await _search_supplier(code, adapter)
                circuit_breaker.record_success(code)
                if res:
                    all_offers.extend(res)
                    logger.info("failover_stop_on_success", supplier=code, offers=len(res))
                    break
            except AppError as e:
                if _is_throttle_error(e):
                    raise
                circuit_breaker.record_failure(code)
            except Exception:
                circuit_breaker.record_failure(code)
    else:
        tasks = [_search_supplier(code, adapter) for code, adapter in runnable]
        codes = [code for code, _ in runnable]
        results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        for code, res in zip(codes, results):
            if isinstance(res, Exception):
                if _is_throttle_error(res):
                    raise res
                circuit_breaker.record_failure(code)
            else:
                circuit_breaker.record_success(code)
                all_offers.extend(res)

    from app.services.offer_aggregation import SortKey, aggregate_offers

    try:
        sort_key = SortKey(query.sort or "recommended")
    except ValueError:
        sort_key = SortKey.recommended

    all_offers, agg_meta = aggregate_offers(
        all_offers,
        sort=sort_key,
        max_stops=query.max_stops,
        airlines=query.airlines,
        max_price=query.max_price,
        depart_time_from=query.depart_time_from,
        depart_time_to=query.depart_time_to,
        limit=50,
        dedupe=bool(query.dedupe),
    )

    search_req = SearchRequest(
        organization_id=current_user.active_organization_id,
        user_id=current_user.id,
        payload=query.model_dump(mode="json"),
    )
    db.add(search_req)
    await db.commit()
    await db.refresh(search_req)

    # Track last search counts for admin (process-local)
    try:
        from app.services.supplier_metrics import record_offer_counts

        record_offer_counts(agg_meta.get("supplier_counts") or {})
    except Exception:
        pass

    # FC Phase 4 — attach display money without mutating supplier fares
    from app.services.fx import (
        attach_offer_money,
        get_fx_quote,
        resolve_display_currency,
    )

    charge_currency = settings.CHARGE_CURRENCY or "INR"
    display_currency = charge_currency
    fx_meta = None
    try:
        display_currency = await resolve_display_currency(
            db, user=current_user, organization_id=org_id
        )
        if display_currency != charge_currency:
            fx_meta = await get_fx_quote(
                db, base=charge_currency, quote=display_currency
            )
        await attach_offer_money(
            all_offers, fx=fx_meta, display_currency=display_currency
        )
    except Exception as e:
        logger.warning("fx_attach_failed", error=str(e))
        display_currency = charge_currency
        await attach_offer_money(
            all_offers, fx=None, display_currency=charge_currency
        )

    return SearchResponse(
        search_request_id=str(search_req.id),
        results_count=len(all_offers),
        offers=all_offers,
        cache_hit=any_cache_hit,
        cache_age_seconds=max(cache_ages) if cache_ages else None,
        supplier_counts=agg_meta.get("supplier_counts"),
        airline_facets=agg_meta.get("airline_facets"),
        aggregation={
            "before_dedupe": agg_meta.get("before_dedupe"),
            "after_dedupe": agg_meta.get("after_dedupe"),
            "deduped_away": agg_meta.get("deduped_away"),
            "sort": agg_meta.get("sort"),
        },
        charge_currency=charge_currency,
        display_currency=display_currency,
        fx_rate=float(fx_meta.rate) if fx_meta else None,
        fx_as_of=fx_meta.as_of.isoformat() if fx_meta and fx_meta.as_of else None,
        fx_source=fx_meta.source if fx_meta else None,
        ancillaries_enabled=bool(settings.FC_ANCILLARIES_ENABLED),
        seat_map_enabled=bool(settings.FC_SEAT_MAP_ENABLED),
    )


async def revalidate_offer(
    request: RevalidateRequest,
    db: Optional[AsyncSession] = None,
    usage_source: str = "user_revalidate",
    org_id=None,
) -> NormalizedOffer:
    """Revalidates an offer via its supplier adapter. Raises AppError with stable codes."""
    try:
        adapter = AdapterRegistry.get_adapter(request.offer.supplier_code)
        if not adapter.capabilities.can_revalidate:
            raise AppError(
                "Supplier does not support revalidation",
                status_code=400,
                error_code="REVALIDATE_UNSUPPORTED",
            )

        result = await adapter.revalidate(request.offer)
        if db is not None:
            await record_live_call(
                db,
                request.offer.supplier_code,
                "revalidate",
                usage_source,
                org_id=org_id,
            )
        return result
    except InventoryRevalidateError as e:
        if db is not None:
            await record_live_call(
                db,
                request.offer.supplier_code,
                "revalidate",
                usage_source,
                org_id=org_id,
            )
        raise AppError(e.message, status_code=409, error_code=e.error_code.upper())
    except AppError:
        raise
    except ValueError as e:
        logger.error("revalidate_adapter_missing", error=str(e))
        raise AppError("Adapter not found for this offer", status_code=500, error_code="ADAPTER_MISSING")
    except Exception as e:
        if db is not None:
            await record_live_call(
                db,
                request.offer.supplier_code,
                "revalidate",
                usage_source,
                org_id=org_id,
            )
        logger.error("revalidate_failed", error=str(e))
        raise AppError(
            f"Revalidation failed: {e}",
            status_code=502,
            error_code="SUPPLIER_ERROR",
        )


async def revalidate_normalized_offer(
    offer: NormalizedOffer,
    db: Optional[AsyncSession] = None,
    usage_source: str = "revalidate",
    org_id=None,
) -> NormalizedOffer:
    """
    Service-level revalidate for payments + worker.
    Propagates InventoryRevalidateError so confirm jobs can map commercial failures.
    """
    adapter = AdapterRegistry.get_adapter(offer.supplier_code)
    if not adapter.capabilities.can_revalidate:
        raise AppError(
            "Supplier does not support revalidation",
            status_code=400,
            error_code="REVALIDATE_UNSUPPORTED",
        )
    try:
        result = await adapter.revalidate(offer)
        if db is not None:
            await record_live_call(
                db, offer.supplier_code, "revalidate", usage_source, org_id=org_id
            )
        return result
    except Exception:
        if db is not None:
            await record_live_call(
                db, offer.supplier_code, "revalidate", usage_source, org_id=org_id
            )
        raise


async def book_offer(
    offer: NormalizedOffer,
    passengers: List[dict],
    db: Optional[AsyncSession] = None,
    usage_source: str = "confirm_book",
    org_id=None,
):
    """
    Service-level book used by background workers.
    Returns BookResult (PNR + optional ticket refs).
    """
    from app.schemas.booking_result import BookResult

    try:
        adapter = AdapterRegistry.get_adapter(offer.supplier_code)
        result = await adapter.book(offer, passengers)
        if isinstance(result, str):
            result = BookResult.from_pnr(result)
        if db is not None:
            await record_live_call(
                db, offer.supplier_code, "book", usage_source, org_id=org_id
            )
        return result
    except ValueError as e:
        logger.error("book_adapter_missing", error=str(e))
        raise AppError("Adapter not found for this offer", status_code=500, error_code="ADAPTER_MISSING")
    except Exception as e:
        if db is not None:
            await record_live_call(
                db, offer.supplier_code, "book", usage_source, org_id=org_id
            )
        logger.error("book_failed", error=str(e))
        raise AppError(f"Booking failed: {e}", status_code=502, error_code="SUPPLIER_ERROR")


async def cancel_booking(supplier_code: str, booking_ref: str) -> bool:
    """
    Service-level cancel used for manual ops or aborts.
    """
    try:
        adapter = AdapterRegistry.get_adapter(supplier_code)
        return await adapter.cancel(booking_ref)
    except Exception as e:
        logger.error("cancel_failed", error=str(e), supplier_code=supplier_code, booking_ref=booking_ref)
        return False
