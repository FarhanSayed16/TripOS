import uuid
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import structlog

from app.schemas.inventory import (
    SearchQuery,
    NormalizedOffer,
    AdapterCapabilities,
    InventoryType,
)
from app.adapters.base import BaseAdapter
from app.core.inventory_errors import InventoryRevalidateError

logger = structlog.get_logger()

class TboClient:
    """
    SIMULATED HTTP client for TBO (not live sandbox).
    Real httpx + credentials are required before Phase 25 exit.
    PNRs are prefixed SIM-TBO so agents never confuse them with live tickets.
    """
    
    async def search_flights(self, origin: str, destination: str, departure_date: str) -> Dict[str, Any]:
        await asyncio.sleep(1.0) # simulate network latency
        
        # Simulate a TBO search response
        return {
            "Response": {
                "ResponseStatus": 1,
                "TraceId": str(uuid.uuid4()),
                "Results": [
                    [
                        {
                            "ResultIndex": "TBO-RES-1",
                            "IsRefundable": True,
                            "Fare": {
                                "Currency": "INR",
                                "BaseFare": 4500,
                                "Tax": 1200,
                                "PublishedFare": 5700
                            },
                            "Segments": [
                                [
                                    {
                                        "Airline": {"AirlineCode": "6E", "AirlineName": "IndiGo"},
                                        "FlightNumber": "302",
                                        "Origin": {"AirportCode": origin},
                                        "Destination": {"AirportCode": destination},
                                        "Duration": 120,
                                        "Baggage": "15 kg"
                                    }
                                ]
                            ]
                        },
                        {
                            "ResultIndex": "TBO-RES-2",
                            "IsRefundable": False,
                            "Fare": {
                                "Currency": "INR",
                                "BaseFare": 3000,
                                "Tax": 1000,
                                "PublishedFare": 4000
                            },
                            "Segments": [
                                [
                                    {
                                        "Airline": {"AirlineCode": "SG", "AirlineName": "SpiceJet"},
                                        "FlightNumber": "415",
                                        "Origin": {"AirportCode": origin},
                                        "Destination": {"AirportCode": destination},
                                        "Duration": 150,
                                        "Baggage": "15 kg"
                                    }
                                ]
                            ]
                        }
                    ]
                ]
            }
        }

    async def fare_quote(self, trace_id: str, result_index: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        
        # Simulate fare change or sold out for specific tokens if needed
        if "FARE-CHG" in result_index:
            return {
                "Response": {
                    "ResponseStatus": 2,
                    "Error": {"ErrorCode": 2, "ErrorMessage": "Fare changed"}
                }
            }
        if "SOLD-OUT" in result_index:
            return {
                "Response": {
                    "ResponseStatus": 3,
                    "Error": {"ErrorCode": 3, "ErrorMessage": "Seat not available"}
                }
            }
            
        # Success response
        return {
            "Response": {
                "ResponseStatus": 1,
                "Results": {
                    "IsPriceChanged": False,
                    "Fare": {
                        "Currency": "INR",
                        "BaseFare": 4500,
                        "Tax": 1200,
                        "PublishedFare": 5700
                    }
                }
            }
        }
        
    async def book(self, trace_id: str, result_index: str, passengers: List[dict]) -> Dict[str, Any]:
        await asyncio.sleep(1.5)
        
        return {
            "Response": {
                "ResponseStatus": 1,
                "Response": {
                    "PNR": f"SIM-TBO{uuid.uuid4().hex[:6].upper()}",
                    "BookingId": str(uuid.uuid4())
                }
            }
        }

    async def cancel(self, pnr: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "Response": {
                "ResponseStatus": 1,
                "TicketStatus": 3 # Cancelled
            }
        }


class TboAdapter(BaseAdapter):
    """
    Adapter for TBO Holidays (Tek Travels).
    Currently SIMULATED — enable in search only via INVENTORY_SUPPLIERS=...,tbo.
    """

    def __init__(self):
        self.client = TboClient()

    @property
    def supplier_code(self) -> str:
        return "tbo"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            can_revalidate=True,
            can_book=True,
            can_cancel=True,
        )

    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        if query.type != InventoryType.FLIGHT:
            return []

        response = await self.client.search_flights(
            origin=query.origin or "DEL",
            destination=query.destination or "BOM",
            departure_date=query.departure_date.strftime("%Y-%m-%d")
        )

        res = response.get("Response", {})
        if res.get("ResponseStatus") != 1:
            logger.error("tbo_search_failed", response=response)
            return []

        trace_id = res.get("TraceId")
        results_array = res.get("Results", [[]])[0]
        
        offers = []
        for item in results_array:
            try:
                result_index = item.get("ResultIndex")
                fare = item.get("Fare", {})
                segments = item.get("Segments", [[]])[0]
                first_segment = segments[0] if segments else {}
                airline = first_segment.get("Airline", {}).get("AirlineName", "Unknown")
                flight_no = first_segment.get("FlightNumber", "")
                
                # We package TraceId and ResultIndex into supplier_reference
                supplier_ref = f"{trace_id}::{result_index}"
                
                offer = NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference=supplier_ref,
                    type=InventoryType.FLIGHT,
                    currency=fare.get("Currency", "INR"),
                    total_amount=float(fare.get("PublishedFare", 0)),
                    base_amount=float(fare.get("BaseFare", 0)),
                    tax_amount=float(fare.get("Tax", 0)),
                    title=f"[SIMULATED] {airline} Flight {flight_no}",
                    description=(
                        f"{first_segment.get('Origin', {}).get('AirportCode')} to "
                        f"{first_segment.get('Destination', {}).get('AirportCode')} "
                        f"({first_segment.get('Duration')} mins) — not a live TBO offer"
                    ),
                    raw_data={**(item or {}), "simulated": True, "provider": "tbo_sim"},
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
                offers.append(offer)
            except Exception as e:
                logger.error("tbo_offer_mapping_failed", error=str(e), raw_item=item)

        return offers

    async def revalidate(self, offer: NormalizedOffer) -> NormalizedOffer:
        try:
            trace_id, result_index = offer.supplier_reference.split("::")
        except ValueError:
            raise InventoryRevalidateError(
                "supplier_error",
                "Invalid supplier_reference format for TBO",
            )

        response = await self.client.fare_quote(trace_id, result_index)
        res = response.get("Response", {})

        status = res.get("ResponseStatus")
        if status == 2:
            raise InventoryRevalidateError(
                "fare_changed",
                "Fare changed during revalidation",
            )
        elif status == 3:
            raise InventoryRevalidateError(
                "sold_out",
                "Seat sold out during revalidation",
            )
        elif status != 1:
            raise InventoryRevalidateError(
                "supplier_error",
                "Unknown error during revalidation",
            )
            
        # In a real scenario, if IsPriceChanged is True, we would update the offer amounts.
        return offer

    async def book(self, offer: NormalizedOffer, passengers: List[Dict[str, Any]]) -> str:
        try:
            trace_id, result_index = offer.supplier_reference.split("::")
        except ValueError:
            raise ValueError("Invalid supplier_reference format for TBO")
            
        response = await self.client.book(trace_id, result_index, passengers)
        res = response.get("Response", {})
        
        if res.get("ResponseStatus") != 1:
            raise Exception("TBO Booking Failed")
            
        pnr = res.get("Response", {}).get("PNR")
        if not pnr:
            raise Exception("TBO Booking succeeded but PNR was missing")
            
        return pnr

    async def cancel(self, booking_ref: str) -> bool:
        response = await self.client.cancel(booking_ref)
        res = response.get("Response", {})
        return res.get("ResponseStatus") == 1

    async def status(self, booking_ref: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "status": "confirmed",
            "supplier_ref": booking_ref,
            "raw": {"ResponseStatus": 1}
        }
