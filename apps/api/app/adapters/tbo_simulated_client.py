"""TBO simulated client — never confuse with live (SIM-TBO PNRs)."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List


class TboSimulatedClient:
    """
    SIMULATED HTTP client for TBO (not live sandbox).
    PNRs are prefixed SIM-TBO so agents never confuse them with live tickets.
    """

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
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
                                "PublishedFare": 5700,
                            },
                            "Segments": [
                                [
                                    {
                                        "Airline": {
                                            "AirlineCode": "6E",
                                            "AirlineName": "IndiGo",
                                        },
                                        "FlightNumber": "302",
                                        "Origin": {"AirportCode": origin},
                                        "Destination": {"AirportCode": destination},
                                        "Duration": 120,
                                        "Baggage": "15 kg",
                                    }
                                ]
                            ],
                        },
                        {
                            "ResultIndex": "TBO-RES-2",
                            "IsRefundable": False,
                            "Fare": {
                                "Currency": "INR",
                                "BaseFare": 3000,
                                "Tax": 1000,
                                "PublishedFare": 4000,
                            },
                            "Segments": [
                                [
                                    {
                                        "Airline": {
                                            "AirlineCode": "SG",
                                            "AirlineName": "SpiceJet",
                                        },
                                        "FlightNumber": "415",
                                        "Origin": {"AirportCode": origin},
                                        "Destination": {"AirportCode": destination},
                                        "Duration": 150,
                                        "Baggage": "15 kg",
                                    }
                                ]
                            ],
                        },
                    ]
                ],
            }
        }

    async def fare_quote(self, trace_id: str, result_index: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        if "FARE-CHG" in result_index:
            return {
                "Response": {
                    "ResponseStatus": 2,
                    "Error": {"ErrorCode": 2, "ErrorMessage": "Fare changed"},
                }
            }
        if "SOLD-OUT" in result_index:
            return {
                "Response": {
                    "ResponseStatus": 3,
                    "Error": {"ErrorCode": 3, "ErrorMessage": "Seat not available"},
                }
            }
        return {
            "Response": {
                "ResponseStatus": 1,
                "Results": {
                    "IsPriceChanged": False,
                    "Fare": {
                        "Currency": "INR",
                        "BaseFare": 4500,
                        "Tax": 1200,
                        "PublishedFare": 5700,
                    },
                },
            }
        }

    async def book(
        self, trace_id: str, result_index: str, passengers: List[dict]
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return {
            "Response": {
                "ResponseStatus": 1,
                "Response": {
                    "PNR": f"SIM-TBO{uuid.uuid4().hex[:6].upper()}",
                    "BookingId": str(uuid.uuid4()),
                    "TicketNumber": None,
                },
            }
        }

    async def ticket(self, trace_id: str, pnr: str, booking_id: Any) -> Dict[str, Any]:
        return {
            "Response": {
                "ResponseStatus": 1,
                "Response": {"PNR": pnr, "BookingId": booking_id},
            }
        }

    async def cancel(self, pnr: str, booking_id: Any = None) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"Response": {"ResponseStatus": 1, "TicketStatus": 3}}

    async def booking_details(
        self, pnr: str, booking_id: Any = None
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "Response": {
                "ResponseStatus": 1,
                "Response": {"PNR": pnr, "BookingStatus": "Confirmed"},
            }
        }
