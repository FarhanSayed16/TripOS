import asyncio
import time
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
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

logger = structlog.get_logger()


from app.services.supplier_strategy import SupplierStrategy
from app.core.circuit_breaker import circuit_breaker

async def search_inventory(
    query: SearchQuery,
    current_user: User,
    db: AsyncSession,
) -> SearchResponse:
    """
    Orchestrates search across configured suppliers using the SupplierStrategy.
    - all: parallel fan-out (asyncio.gather)
    - primary_only: only first configured supplier
    - failover: sequential; stop after first supplier that returns offers
    """
    strategy = SupplierStrategy()
    mode = strategy.get_strategy()
    active_supplier_codes = await strategy.select_for_search(query)
    logger.info("inventory_search_suppliers", suppliers=active_supplier_codes, strategy=mode)

    async def _timed_search(adapter, q):
        start_time = time.time()
        try:
            res = await adapter.search(q)
            logger.info(
                "supplier_search_success",
                supplier=adapter.supplier_code,
                duration_ms=int((time.time() - start_time) * 1000),
            )
            return res
        except Exception as e:
            logger.error(
                "supplier_search_error",
                supplier=adapter.supplier_code,
                duration_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )
            raise e

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

    if mode == "failover":
        for code, adapter in runnable:
            try:
                res = await _timed_search(adapter, query)
                circuit_breaker.record_success(code)
                if res:
                    all_offers.extend(res)
                    logger.info("failover_stop_on_success", supplier=code, offers=len(res))
                    break
            except Exception:
                circuit_breaker.record_failure(code)
    else:
        # all + primary_only: parallel among selected adapters
        tasks = [_timed_search(adapter, query) for _, adapter in runnable]
        codes = [code for code, _ in runnable]
        results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        for code, res in zip(codes, results):
            if isinstance(res, Exception):
                circuit_breaker.record_failure(code)
            else:
                circuit_breaker.record_success(code)
                all_offers.extend(res)

    all_offers.sort(key=lambda o: o.total_amount)
    all_offers = all_offers[:50]

    search_req = SearchRequest(
        organization_id=current_user.active_organization_id,
        user_id=current_user.id,
        payload=query.model_dump(mode="json"),
    )
    db.add(search_req)
    await db.commit()
    await db.refresh(search_req)

    return SearchResponse(
        search_request_id=str(search_req.id),
        results_count=len(all_offers),
        offers=all_offers,
    )


async def revalidate_offer(request: RevalidateRequest) -> NormalizedOffer:
    """Revalidates an offer via its supplier adapter. Raises AppError with stable codes."""
    try:
        adapter = AdapterRegistry.get_adapter(request.offer.supplier_code)
        if not adapter.capabilities.can_revalidate:
            raise AppError(
                "Supplier does not support revalidation",
                status_code=400,
                error_code="REVALIDATE_UNSUPPORTED",
            )

        return await adapter.revalidate(request.offer)
    except InventoryRevalidateError as e:
        raise AppError(e.message, status_code=409, error_code=e.error_code.upper())
    except AppError:
        raise
    except ValueError as e:
        logger.error("revalidate_adapter_missing", error=str(e))
        raise AppError("Adapter not found for this offer", status_code=500, error_code="ADAPTER_MISSING")
    except Exception as e:
        logger.error("revalidate_failed", error=str(e))
        raise AppError(
            f"Revalidation failed: {e}",
            status_code=502,
            error_code="SUPPLIER_ERROR",
        )


async def revalidate_normalized_offer(offer: NormalizedOffer) -> NormalizedOffer:
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
    return await adapter.revalidate(offer)


async def book_offer(offer: NormalizedOffer, passengers: List[dict]) -> str:
    """
    Service-level book used by background workers.
    Returns the supplier PNR.
    """
    try:
        adapter = AdapterRegistry.get_adapter(offer.supplier_code)
        return await adapter.book(offer, passengers)
    except ValueError as e:
        logger.error("book_adapter_missing", error=str(e))
        raise AppError("Adapter not found for this offer", status_code=500, error_code="ADAPTER_MISSING")
    except Exception as e:
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
