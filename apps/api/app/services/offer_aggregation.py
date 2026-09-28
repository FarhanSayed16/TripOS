"""Offer aggregation: fingerprint, dedupe, rank, filter (FC Phase 3)."""
from __future__ import annotations

import re
from collections import Counter
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.inventory import InventoryType, NormalizedOffer


class SortKey(str, Enum):
    price = "price"
    duration = "duration"
    stops = "stops"
    recommended = "recommended"


def enrich_offer_fields(offer: NormalizedOffer) -> NormalizedOffer:
    """
    Fill duration_minutes / stops / airline_* / source_type from raw_data when missing.
    Mutates a copy — safe for cached offers.
    """
    o = offer.model_copy(deep=True)
    raw = dict(o.raw_data or {})

    if o.source_type is None:
        o.source_type = _infer_source_type(o.supplier_code, raw)

    if o.type == InventoryType.FLIGHT:
        if o.duration_minutes is None:
            o.duration_minutes = _extract_duration(raw, o.description)
        if o.stops is None:
            o.stops = _extract_stops(raw, o.description)
        if not o.airline_code or not o.airline_name:
            code, name = _extract_airline(raw, o.title)
            o.airline_code = o.airline_code or code
            o.airline_name = o.airline_name or name
        if o.depart_time is None:
            o.depart_time = _extract_depart_time(raw)
    else:
        # Hotels: map "stars" / nights loosely; stops unused
        if o.stops is None:
            o.stops = 0
        if o.duration_minutes is None:
            o.duration_minutes = None

    return o


def _infer_source_type(supplier_code: str, raw: Dict[str, Any]) -> str:
    explicit = raw.get("source_type") or raw.get("SourceType")
    if explicit:
        return str(explicit).lower()
    code = (supplier_code or "").lower()
    if code in ("mock_supplier",):
        return "mock"
    if code in ("tbo", "tripjack"):
        return "agg"
    return "agg"


def _extract_duration(raw: Dict[str, Any], description: Optional[str]) -> Optional[int]:
    try:
        segments = raw.get("Segments") or []
        if segments and segments[0]:
            total = 0
            for seg in segments[0]:
                d = seg.get("Duration") or seg.get("DurationMinutes")
                if d is not None:
                    total += int(d)
            if total:
                return total
    except (TypeError, ValueError, IndexError):
        pass
    if description:
        m = re.search(r"\((\d+)\s*mins?\)", description, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"(\d+)\s*h(?:ours?)?\s*(\d+)?\s*m?", description, re.I)
        if m:
            hours = int(m.group(1))
            mins = int(m.group(2) or 0)
            return hours * 60 + mins
    return None


def _extract_stops(raw: Dict[str, Any], description: Optional[str]) -> Optional[int]:
    try:
        segments = raw.get("Segments") or []
        if segments and segments[0]:
            n = len(segments[0])
            return max(0, n - 1)
    except (TypeError, IndexError):
        pass
    if description:
        if re.search(r"non[\s-]?stop", description, re.I):
            return 0
        m = re.search(r"(\d+)\s*stop", description, re.I)
        if m:
            return int(m.group(1))
    return None


def _extract_airline(raw: Dict[str, Any], title: str) -> Tuple[Optional[str], Optional[str]]:
    if raw.get("airline") or raw.get("AirlineName"):
        name = raw.get("AirlineName") or raw.get("airline")
        code = raw.get("AirlineCode") or raw.get("airline_code")
        return (str(code) if code else None, str(name) if name else None)
    try:
        segments = raw.get("Segments") or []
        if segments and segments[0]:
            airline = segments[0][0].get("Airline") or {}
            return airline.get("AirlineCode"), airline.get("AirlineName")
    except (TypeError, IndexError, KeyError):
        pass
    # Title like "IndiGo Flight 302" or "[SIMULATED] IndiGo Flight 302"
    clean = re.sub(r"^\[SIMULATED\]\s*", "", title or "")
    m = re.match(r"(.+?)\s+Flight\b", clean, re.I)
    if m:
        return None, m.group(1).strip()
    return None, None


def _extract_depart_time(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("DepTime", "DepartureTime", "PreferredDepartureTime"):
        val = raw.get(key)
        if val and isinstance(val, str) and len(val) >= 16:
            # ISO-ish …T14:30:00
            try:
                return val[11:16]
            except Exception:
                pass
    try:
        segments = raw.get("Segments") or []
        if segments and segments[0]:
            origin = segments[0][0].get("Origin") or {}
            dep = origin.get("DepTime") or segments[0][0].get("DepTime")
            if dep and isinstance(dep, str) and "T" in dep:
                return dep.split("T")[1][:5]
    except (TypeError, IndexError, KeyError):
        pass
    return None


def flight_fingerprint(offer: NormalizedOffer) -> str:
    """
    Same logical flight across suppliers → one fingerprint.
    Prefer structured fields; fall back to title+route hints.
    """
    o = enrich_offer_fields(offer)
    raw = o.raw_data or {}
    flight_no = ""
    try:
        segments = raw.get("Segments") or []
        if segments and segments[0]:
            flight_no = str(segments[0][0].get("FlightNumber") or "")
    except (TypeError, IndexError):
        pass
    if not flight_no and raw.get("flight_number"):
        flight_no = str(raw.get("flight_number"))
    airline = (o.airline_code or o.airline_name or "").upper()
    dep = o.depart_time or ""
    duration = o.duration_minutes if o.duration_minutes is not None else ""
    stops = o.stops if o.stops is not None else ""
    # Include type so hotels never collide with flights
    return f"{o.type.value}|{airline}|{flight_no}|{dep}|{duration}|{stops}|{o.title}".lower()


def hotel_fingerprint(offer: NormalizedOffer) -> str:
    o = enrich_offer_fields(offer)
    raw = o.raw_data or {}
    hotel_id = raw.get("hotel_id") or raw.get("HotelCode") or o.supplier_reference
    return f"hotel|{hotel_id}|{o.title}".lower()


def fingerprint(offer: NormalizedOffer) -> str:
    if offer.type == InventoryType.HOTEL:
        return hotel_fingerprint(offer)
    return flight_fingerprint(offer)


# Preferred supplier when prices tie (live agg over mock)
_SUPPLIER_PREF = {"tbo": 0, "tripjack": 1, "mock_supplier": 9}


def dedupe_offers(
    offers: List[NormalizedOffer],
    *,
    prefer_cheapest: bool = True,
) -> List[NormalizedOffer]:
    """Keep one offer per fingerprint — cheapest, then preferred supplier."""
    enriched = [enrich_offer_fields(o) for o in offers]
    best: Dict[str, NormalizedOffer] = {}
    for o in enriched:
        key = fingerprint(o)
        prev = best.get(key)
        if prev is None:
            best[key] = o
            continue
        if prefer_cheapest:
            if o.total_amount < prev.total_amount:
                best[key] = o
            elif o.total_amount == prev.total_amount:
                if _SUPPLIER_PREF.get(o.supplier_code, 5) < _SUPPLIER_PREF.get(
                    prev.supplier_code, 5
                ):
                    best[key] = o
        else:
            if _SUPPLIER_PREF.get(o.supplier_code, 5) < _SUPPLIER_PREF.get(
                prev.supplier_code, 5
            ):
                best[key] = o
    return list(best.values())


def _recommended_score(o: NormalizedOffer) -> Tuple[float, float, int]:
    """Lower is better: price weight + duration + stops."""
    price = float(o.total_amount or 0)
    dur = float(o.duration_minutes if o.duration_minutes is not None else 9999)
    stops = int(o.stops if o.stops is not None else 9)
    # Normalize roughly: price primary, then duration, then stops
    return (price + dur * 2 + stops * 500, dur, stops)


def sort_offers(offers: List[NormalizedOffer], sort: SortKey) -> List[NormalizedOffer]:
    items = [enrich_offer_fields(o) for o in offers]
    if sort == SortKey.price:
        return sorted(items, key=lambda o: (o.total_amount, o.title or ""))
    if sort == SortKey.duration:
        return sorted(
            items,
            key=lambda o: (
                o.duration_minutes if o.duration_minutes is not None else 10**9,
                o.total_amount,
            ),
        )
    if sort == SortKey.stops:
        return sorted(
            items,
            key=lambda o: (
                o.stops if o.stops is not None else 10**9,
                o.total_amount,
            ),
        )
    # recommended
    return sorted(items, key=_recommended_score)


def filter_offers(
    offers: List[NormalizedOffer],
    *,
    max_stops: Optional[int] = None,
    airlines: Optional[List[str]] = None,
    max_price: Optional[float] = None,
    depart_time_from: Optional[str] = None,  # "HH:MM"
    depart_time_to: Optional[str] = None,
) -> List[NormalizedOffer]:
    airline_set = {a.upper() for a in (airlines or []) if a}

    def _ok(o: NormalizedOffer) -> bool:
        o = enrich_offer_fields(o)
        if max_stops is not None and o.stops is not None and o.stops > max_stops:
            return False
        if max_price is not None and o.total_amount > max_price:
            return False
        if airline_set:
            code = (o.airline_code or "").upper()
            name = (o.airline_name or "").upper()
            if code not in airline_set and name not in airline_set:
                # also allow partial name match
                if not any(a in name for a in airline_set):
                    return False
        if o.depart_time and (depart_time_from or depart_time_to):
            t = o.depart_time
            if depart_time_from and t < depart_time_from:
                return False
            if depart_time_to and t > depart_time_to:
                return False
        return True

    return [enrich_offer_fields(o) for o in offers if _ok(o)]


def supplier_counts(offers: List[NormalizedOffer]) -> Dict[str, int]:
    return dict(Counter(o.supplier_code for o in offers))


def airline_facets(offers: List[NormalizedOffer]) -> List[Dict[str, Any]]:
    c: Counter = Counter()
    for o in offers:
        o = enrich_offer_fields(o)
        label = o.airline_code or o.airline_name
        if label:
            c[label] += 1
    return [{"airline": k, "count": v} for k, v in sorted(c.items())]


def aggregate_offers(
    offers: List[NormalizedOffer],
    *,
    sort: SortKey = SortKey.recommended,
    max_stops: Optional[int] = None,
    airlines: Optional[List[str]] = None,
    max_price: Optional[float] = None,
    depart_time_from: Optional[str] = None,
    depart_time_to: Optional[str] = None,
    limit: int = 50,
    dedupe: bool = True,
) -> Tuple[List[NormalizedOffer], Dict[str, Any]]:
    """
    Full pipeline: enrich → dedupe → filter → sort → limit.
    Returns (offers, meta with counts/facets).
    """
    working = [enrich_offer_fields(o) for o in offers]
    before_dedupe = len(working)
    if dedupe:
        working = dedupe_offers(working)
    after_dedupe = len(working)
    working = filter_offers(
        working,
        max_stops=max_stops,
        airlines=airlines,
        max_price=max_price,
        depart_time_from=depart_time_from,
        depart_time_to=depart_time_to,
    )
    working = sort_offers(working, sort)
    meta = {
        "before_dedupe": before_dedupe,
        "after_dedupe": after_dedupe,
        "deduped_away": max(0, before_dedupe - after_dedupe),
        "supplier_counts": supplier_counts(working),
        "airline_facets": airline_facets(working),
        "sort": sort.value,
    }
    return working[:limit], meta
