"""Fare rules resolution (FC Phase 2)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.adapters.registry import AdapterRegistry
from app.schemas.fare_rules import FareRules
from app.schemas.inventory import NormalizedOffer


def _boolish(val: Any) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "y"):
        return True
    if s in ("0", "false", "no", "n"):
        return False
    return None


def derive_fare_rules_from_offer(offer: NormalizedOffer) -> FareRules:
    raw: Dict[str, Any] = dict(offer.raw_data or {})
    is_refundable = _boolish(raw.get("IsRefundable") if "IsRefundable" in raw else raw.get("is_refundable"))
    baggage = None
    segments = raw.get("Segments") or []
    try:
        if segments and segments[0] and segments[0][0]:
            baggage = segments[0][0].get("Baggage")
    except (IndexError, TypeError, KeyError):
        pass
    if not baggage:
        baggage = raw.get("baggage") or raw.get("Baggage")

    if is_refundable is True:
        cancel_summary = "Refundable fare — cancellation may incur airline penalties; confirm before cancel."
        change_summary = "Changes may be allowed with fare difference + fees."
        change_allowed = True
    elif is_refundable is False:
        cancel_summary = "Non-refundable fare — cancellation typically forfeits most of the amount."
        change_summary = "Changes often restricted or not permitted on this fare."
        change_allowed = False
    else:
        cancel_summary = "Cancellation terms not provided by supplier — treat as restricted until confirmed."
        change_summary = "Change terms not provided by supplier — revalidate before promising changes."
        change_allowed = None

    # Mock fixtures: include baggage from description when present
    if not baggage and offer.description and "kg" in offer.description.lower():
        baggage = "See offer description"

    lines = [
        f"Supplier: {offer.supplier_code}",
        f"Refundable: {is_refundable if is_refundable is not None else 'unknown'}",
        f"Cancel: {cancel_summary}",
        f"Change: {change_summary}",
    ]
    if baggage:
        lines.append(f"Baggage: {baggage}")

    return FareRules(
        supplier_code=offer.supplier_code,
        supplier_reference=offer.supplier_reference,
        is_refundable=is_refundable,
        change_allowed=change_allowed,
        cancel_penalty_summary=cancel_summary,
        change_penalty_summary=change_summary,
        baggage_summary=str(baggage) if baggage else None,
        raw_text="\n".join(lines),
        source="derived",
    )


async def get_fare_rules_for_offer(offer: NormalizedOffer) -> FareRules:
    """Prefer adapter-specific rules when implemented; else derive from offer payload."""
    try:
        adapter = AdapterRegistry.get_adapter(offer.supplier_code)
    except ValueError:
        return derive_fare_rules_from_offer(offer)

    fare_fn = getattr(adapter, "fare_rules", None)
    if callable(fare_fn):
        try:
            result = await fare_fn(offer)
            if isinstance(result, FareRules):
                return result
        except Exception:
            pass
    return derive_fare_rules_from_offer(offer)
