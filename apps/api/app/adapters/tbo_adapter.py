"""TBO adapter — live HTTP when enabled, else honest SIMULATED client (FC Phase 1)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import structlog

from app.adapters.base import BaseAdapter
from app.adapters.tbo_live_client import TboLiveClient, TboLiveError
from app.adapters.tbo_simulated_client import TboSimulatedClient
from app.core.config import settings
from app.core.inventory_errors import InventoryRevalidateError
from app.schemas.booking_result import BookResult
from app.schemas.inventory import (
    AdapterCapabilities,
    InventoryType,
    NormalizedOffer,
    SearchQuery,
    FlightSegment,
)

logger = structlog.get_logger()


def _airport_code(node: Any) -> Optional[str]:
    if not isinstance(node, dict):
        return None
    return node.get("AirportCode") or node.get("CityCode")


def _map_tbo_segments(segments_raw: Any) -> List[FlightSegment]:
    """
    TBO Results[].Segments is typically List[List[segment]] (legs → segments).
    Flatten into TripOS FlightSegment with marketing vs operating carrier.
    """
    out: List[FlightSegment] = []
    if not segments_raw:
        return out
    legs = segments_raw
    # Normalize to list of legs
    if isinstance(legs, dict):
        legs = [legs]
    if not isinstance(legs, list):
        return out
    # If flat list of segment dicts (not nested), wrap
    if legs and isinstance(legs[0], dict) and "Origin" in legs[0]:
        legs = [legs]

    for leg in legs:
        if not isinstance(leg, list):
            continue
        for seg in leg:
            if not isinstance(seg, dict):
                continue
            airline = seg.get("Airline") or {}
            op = seg.get("OperatingCarrier") or seg.get("OperatingAirline") or {}
            if isinstance(op, str):
                op_code = op
            else:
                op_code = (op or {}).get("AirlineCode") or (op or {}).get("Code")
            mkt_code = airline.get("AirlineCode") if isinstance(airline, dict) else None
            flight_no = seg.get("FlightNumber") or airline.get("FlightNumber")
            if mkt_code and flight_no and not str(flight_no).upper().startswith(str(mkt_code).upper()):
                flight_display = f"{mkt_code}{flight_no}"
            else:
                flight_display = str(flight_no) if flight_no else None
            duration = seg.get("Duration")
            try:
                duration_i = int(duration) if duration is not None else None
            except (TypeError, ValueError):
                duration_i = None
            out.append(
                FlightSegment(
                    origin=_airport_code(seg.get("Origin") or {}) or "",
                    destination=_airport_code(seg.get("Destination") or {}) or "",
                    departure_at=seg.get("DepTime") or seg.get("DepartureTime"),
                    arrival_at=seg.get("ArrTime") or seg.get("ArrivalTime"),
                    marketing_carrier=mkt_code,
                    operating_carrier=op_code or mkt_code,
                    flight_number=flight_display,
                    duration_minutes=duration_i,
                    cabin=(seg.get("CabinClass") or seg.get("Cabin") or None),
                )
            )
    return [s for s in out if s.origin or s.destination]


def tbo_live_mode_active() -> bool:
    """True only when explicitly enabled and credentials are present."""
    if not settings.TBO_LIVE_ENABLED:
        return False
    client = TboLiveClient()
    return client.credentials_ready()


class TboAdapter(BaseAdapter):
    """
    Adapter for TBO Holidays (Tek Travels).

    - TBO_LIVE_ENABLED=true + creds → live httpx client; titles without [SIMULATED]
    - Otherwise → simulated client; titles/PNRs clearly marked SIM
    """

    def __init__(self) -> None:
        self._live = tbo_live_mode_active()
        self.client: Any = TboLiveClient() if self._live else TboSimulatedClient()
        logger.info(
            "tbo_adapter_init",
            live=self._live,
            live_flag=settings.TBO_LIVE_ENABLED,
        )

    @property
    def supplier_code(self) -> str:
        return "tbo"

    @property
    def inventory_mode(self) -> str:
        return "live" if self._live else "simulated"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            can_revalidate=True,
            can_book=True,
            can_cancel=True,
        )

    def map_error(self, exc: Exception) -> InventoryRevalidateError:
        if isinstance(exc, InventoryRevalidateError):
            return exc
        if isinstance(exc, TboLiveError):
            msg = str(exc).lower()
            if "timeout" in msg:
                return InventoryRevalidateError("supplier_timeout", str(exc))
            return InventoryRevalidateError("supplier_error", str(exc))
        return super().map_error(exc)

    def _unwrap_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response.get("Response") or response

    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        if query.type != InventoryType.FLIGHT:
            return []

        try:
            response = await self.client.search_flights(
                origin=query.origin or "DEL",
                destination=query.destination or "BOM",
                departure_date=query.departure_date.strftime("%Y-%m-%d"),
                adults=query.passengers.adults,
                children=query.passengers.children,
                infants=query.passengers.infants,
                return_date=(
                    query.return_date.strftime("%Y-%m-%d") if query.return_date else None
                ),
            )
        except TboLiveError as e:
            logger.error("tbo_search_live_failed", error=str(e), raw=getattr(e, "raw", None))
            raise self.map_error(e)

        res = self._unwrap_response(response)
        status = res.get("ResponseStatus", response.get("ResponseStatus"))
        if status is not None and int(status) != 1:
            logger.error("tbo_search_failed", response=response)
            return []

        trace_id = res.get("TraceId") or response.get("TraceId")
        results_root = res.get("Results") or response.get("Results") or [[]]
        if isinstance(results_root, list) and results_root and isinstance(results_root[0], list):
            results_array = results_root[0]
        elif isinstance(results_root, list):
            results_array = results_root
        else:
            results_array = []

        offers: List[NormalizedOffer] = []
        mode = self.inventory_mode
        for item in results_array:
            try:
                result_index = item.get("ResultIndex")
                fare = item.get("Fare", {}) or {}
                segments = item.get("Segments", [[]]) or [[]]
                first_leg = segments[0] if segments else []
                first_segment = first_leg[0] if first_leg else {}
                airline = (first_segment.get("Airline") or {}).get("AirlineName", "Unknown")
                airline_code = (first_segment.get("Airline") or {}).get("AirlineCode")
                flight_no = first_segment.get("FlightNumber", "")
                duration = first_segment.get("Duration")
                mapped_segments = _map_tbo_segments(segments)
                try:
                    if mapped_segments:
                        stops = max(0, len(mapped_segments) - 1)
                    else:
                        stops = max(0, len(segments) - 1) if segments else 0
                except TypeError:
                    stops = 0

                supplier_ref = f"{trace_id}::{result_index}"
                title_core = f"{airline} Flight {flight_no}".strip()
                title = title_core if mode == "live" else f"[SIMULATED] {title_core}"
                desc_bits = [
                    f"{(first_segment.get('Origin') or {}).get('AirportCode')} to "
                    f"{(first_segment.get('Destination') or {}).get('AirportCode')}",
                    f"({first_segment.get('Duration')} mins)",
                ]
                if mode != "live":
                    desc_bits.append("— not a live TBO offer")

                dep_time = None
                if first_segment.get("DepTime"):
                    # Often ISO; show HH:MM when possible
                    raw_dep = str(first_segment.get("DepTime"))
                    dep_time = raw_dep[11:16] if "T" in raw_dep and len(raw_dep) >= 16 else raw_dep

                offer = NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference=supplier_ref,
                    type=InventoryType.FLIGHT,
                    currency=fare.get("Currency", "INR"),
                    total_amount=float(fare.get("PublishedFare", 0) or 0),
                    base_amount=float(fare.get("BaseFare", 0) or 0),
                    tax_amount=float(fare.get("Tax", 0) or 0),
                    title=title,
                    description=" ".join(desc_bits),
                    raw_data={
                        **(item or {}),
                        "simulated": mode != "live",
                        "inventory_mode": mode,
                        "provider": "tbo",
                        "TraceId": trace_id,
                        "source_type": "agg",
                    },
                    inventory_mode=mode,
                    source_type="agg",
                    duration_minutes=int(duration) if duration is not None else None,
                    stops=stops,
                    airline_code=airline_code,
                    airline_name=airline,
                    depart_time=dep_time,
                    segments=mapped_segments or None,
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
                offers.append(offer)
            except Exception as e:
                logger.error("tbo_offer_mapping_failed", error=str(e), raw_item=item)

        return offers

    async def revalidate(self, offer: NormalizedOffer) -> NormalizedOffer:
        try:
            trace_id, result_index = offer.supplier_reference.split("::", 1)
        except ValueError as e:
            raise InventoryRevalidateError(
                "supplier_error",
                "Invalid supplier_reference format for TBO",
            ) from e

        try:
            response = await self.client.fare_quote(trace_id, result_index)
        except TboLiveError as e:
            raise self.map_error(e) from e

        res = self._unwrap_response(response)
        status = res.get("ResponseStatus")
        if status == 2 or (res.get("Error") or {}).get("ErrorCode") == 2:
            raise InventoryRevalidateError(
                "fare_changed",
                "Fare changed during revalidation",
            )
        if status == 3 or (res.get("Error") or {}).get("ErrorCode") == 3:
            raise InventoryRevalidateError(
                "sold_out",
                "Seat sold out during revalidation",
            )
        if status is not None and int(status) != 1:
            err = (res.get("Error") or {}).get("ErrorMessage") or "Unknown revalidate error"
            raise InventoryRevalidateError("supplier_error", str(err))

        results = res.get("Results") or {}
        fare = results.get("Fare") if isinstance(results, dict) else None
        updated = offer.model_copy(deep=True)
        updated.is_revalidated = True
        updated.inventory_mode = self.inventory_mode
        if isinstance(fare, dict) and fare.get("PublishedFare") is not None:
            new_total = float(fare.get("PublishedFare") or 0)
            if offer.total_amount and abs(new_total - float(offer.total_amount)) > 0.01:
                # Some TBO flows return changed fare with status 1 + IsPriceChanged
                if results.get("IsPriceChanged"):
                    raise InventoryRevalidateError(
                        "fare_changed",
                        f"Fare changed: was {offer.total_amount}, now {new_total}",
                    )
            updated.total_amount = new_total
            updated.base_amount = float(fare.get("BaseFare") or updated.base_amount)
            updated.tax_amount = float(fare.get("Tax") or updated.tax_amount)
            updated.currency = fare.get("Currency") or updated.currency
        return updated

    async def book(self, offer: NormalizedOffer, passengers: List[Dict[str, Any]]) -> BookResult:
        try:
            trace_id, result_index = offer.supplier_reference.split("::", 1)
        except ValueError as e:
            raise ValueError("Invalid supplier_reference format for TBO") from e

        try:
            response = await self.client.book(trace_id, result_index, passengers)
        except TboLiveError as e:
            raise self.map_error(e) from e

        res = self._unwrap_response(response)
        if res.get("ResponseStatus") is not None and int(res.get("ResponseStatus")) != 1:
            raise Exception(f"TBO Booking Failed: {res.get('Error') or res}")

        inner = res.get("Response") if isinstance(res.get("Response"), dict) else res
        pnr = inner.get("PNR") or res.get("PNR")
        if not pnr:
            raise Exception("TBO Booking succeeded but PNR was missing")

        booking_id = inner.get("BookingId") or res.get("BookingId")
        ticket_numbers: List[str] = []
        for key in ("TicketNumber", "TicketNo", "TicketId"):
            val = inner.get(key) or res.get(key)
            if val:
                ticket_numbers.append(str(val))
                break

        ticket_url = (
            inner.get("InvoicePath")
            or inner.get("TicketPath")
            or inner.get("DocumentUrl")
            or None
        )

        # Optional ticketing step for live LCC/GDS flows that separate Book vs Ticket
        if self._live and settings.TBO_AUTO_TICKET and booking_id:
            try:
                ticket_resp = await self.client.ticket(trace_id, pnr, booking_id)
                t_inner = self._unwrap_response(ticket_resp)
                t_body = (
                    t_inner.get("Response")
                    if isinstance(t_inner.get("Response"), dict)
                    else t_inner
                )
                tn = t_body.get("TicketNumber") or t_body.get("TicketNo")
                if tn and str(tn) not in ticket_numbers:
                    ticket_numbers.append(str(tn))
                ticket_url = (
                    t_body.get("InvoicePath")
                    or t_body.get("TicketPath")
                    or ticket_url
                )
            except Exception as e:
                logger.warning("tbo_auto_ticket_failed", error=str(e), pnr=pnr)

        return BookResult(
            pnr=str(pnr),
            supplier_booking_id=str(booking_id) if booking_id else None,
            ticket_numbers=ticket_numbers,
            ticket_document_url=ticket_url,
            raw={"response": response, "inventory_mode": self.inventory_mode},
        )

    async def cancel(self, booking_ref: str) -> bool:
        try:
            response = await self.client.cancel(booking_ref)
        except TboLiveError as e:
            logger.error("tbo_cancel_failed", error=str(e))
            return False
        res = self._unwrap_response(response)
        status = res.get("ResponseStatus")
        return status is None or int(status) == 1

    async def status(self, booking_ref: str) -> Dict[str, Any]:
        try:
            response = await self.client.booking_details(booking_ref)
        except TboLiveError as e:
            return {
                "status": "unknown",
                "supplier_ref": booking_ref,
                "raw": {"error": str(e)},
            }
        res = self._unwrap_response(response)
        inner = res.get("Response") if isinstance(res.get("Response"), dict) else res
        return {
            "status": str(inner.get("BookingStatus") or "confirmed").lower(),
            "supplier_ref": booking_ref,
            "raw": response,
        }
