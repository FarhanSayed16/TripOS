import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from app.schemas.inventory import (
    SearchQuery,
    NormalizedOffer,
    AdapterCapabilities,
    InventoryType,
)
from app.adapters.base import BaseAdapter
from app.core.inventory_errors import InventoryRevalidateError


class MockAdapter(BaseAdapter):
    """
    Deterministic mock adapter for TripOS without live supplier APIs.

    Revalidate failure simulations (Sprint E):
    - supplier_reference containing ``FARE-CHG`` → fare_changed
    - supplier_reference containing ``SOLD-OUT`` → sold_out
    """

    @property
    def supplier_code(self) -> str:
        return "mock_supplier"

    @property
    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            can_revalidate=True,
            can_book=True,
            can_cancel=True,
        )

    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        offers = []
        if query.type == InventoryType.FLIGHT:
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-FLIGHT-001",
                    type=InventoryType.FLIGHT,
                    currency="INR",
                    total_amount=15000.0,
                    base_amount=12000.0,
                    tax_amount=3000.0,
                    title=f"Mock Flight: {query.origin} to {query.destination}",
                    description="Non-stop, 2h 30m. Includes 15kg checked baggage.",
                    inventory_mode="mock",
                    source_type="mock",
                    duration_minutes=150,
                    stops=0,
                    airline_code="MK",
                    airline_name="MockAir",
                    depart_time="08:00",
                    raw_data={
                        "airline": "MockAir",
                        "airline_code": "MK",
                        "flight_number": "MK101",
                        "inventory_mode": "mock",
                        "provider": "mock_supplier",
                    },
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
            )
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-FLIGHT-002",
                    type=InventoryType.FLIGHT,
                    currency="INR",
                    total_amount=12500.0,
                    base_amount=10000.0,
                    tax_amount=2500.0,
                    title=f"Mock Economy Flight: {query.origin} to {query.destination}",
                    description="1 stop, 5h 00m. Basic economy.",
                    inventory_mode="mock",
                    source_type="mock",
                    duration_minutes=300,
                    stops=1,
                    airline_code="MB",
                    airline_name="MockBudget",
                    depart_time="14:30",
                    raw_data={
                        "airline": "MockBudget",
                        "flight_number": "MB202",
                        "inventory_mode": "mock",
                    },
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
            )
            # Deterministic failure fixtures for revalidate-before-pay tests
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-FLIGHT-FARE-CHG",
                    type=InventoryType.FLIGHT,
                    currency="INR",
                    total_amount=14000.0,
                    base_amount=11000.0,
                    tax_amount=3000.0,
                    title=f"Mock Fare-Risk Flight: {query.origin} to {query.destination}",
                    description="Revalidate will simulate fare_changed (for agent testing).",
                    inventory_mode="mock",
                    source_type="mock",
                    duration_minutes=180,
                    stops=0,
                    airline_code="MR",
                    airline_name="MockRisk",
                    depart_time="10:15",
                    raw_data={"airline": "MockRisk", "simulate": "fare_changed", "inventory_mode": "mock"},
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
            )
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-FLIGHT-SOLD-OUT",
                    type=InventoryType.FLIGHT,
                    currency="INR",
                    total_amount=9900.0,
                    base_amount=8000.0,
                    tax_amount=1900.0,
                    title=f"Mock Sold-Out Flight: {query.origin} to {query.destination}",
                    description="Revalidate will simulate sold_out (for agent testing).",
                    inventory_mode="mock",
                    source_type="mock",
                    duration_minutes=160,
                    stops=0,
                    airline_code="MG",
                    airline_name="MockGone",
                    depart_time="19:45",
                    raw_data={"airline": "MockGone", "simulate": "sold_out", "inventory_mode": "mock"},
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=15),
                )
            )
        elif query.type == InventoryType.HOTEL:
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-HOTEL-001",
                    type=InventoryType.HOTEL,
                    currency="INR",
                    total_amount=8500.0,
                    base_amount=7000.0,
                    tax_amount=1500.0,
                    title=f"Mock Luxury Hotel in {query.destination}",
                    description="Deluxe King Room with Sea View. Breakfast included.",
                    inventory_mode="mock",
                    source_type="mock",
                    stops=0,
                    raw_data={"hotel_id": "H100", "room_type": "DLX", "inventory_mode": "mock"},
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=30),
                )
            )
            offers.append(
                NormalizedOffer(
                    id=str(uuid.uuid4()),
                    supplier_code=self.supplier_code,
                    supplier_reference="MOCK-HOTEL-SOLD-OUT",
                    type=InventoryType.HOTEL,
                    currency="INR",
                    total_amount=6000.0,
                    base_amount=5000.0,
                    tax_amount=1000.0,
                    title=f"Mock Sold-Out Hotel in {query.destination}",
                    description="Revalidate will simulate sold_out (for agent testing).",
                    inventory_mode="mock",
                    source_type="mock",
                    stops=0,
                    raw_data={"hotel_id": "H999", "simulate": "sold_out", "inventory_mode": "mock"},
                    valid_until=datetime.now(timezone.utc) + timedelta(minutes=30),
                )
            )

        return offers

    async def revalidate(self, offer: NormalizedOffer) -> NormalizedOffer:
        ref = (offer.supplier_reference or "").upper()
        simulate = (offer.raw_data or {}).get("simulate")

        if "SOLD-OUT" in ref or simulate == "sold_out":
            raise InventoryRevalidateError(
                "sold_out",
                "This offer is no longer available with the supplier.",
            )

        if "FARE-CHG" in ref or simulate == "fare_changed":
            prev_paise = int(round(float(offer.total_amount) * 100))
            new_paise = int(round(prev_paise * 1.08))  # +8% for agent UX testing
            raise InventoryRevalidateError(
                "fare_changed",
                (
                    f"Fare changed. Previous total was {offer.currency} "
                    f"{offer.total_amount:.2f}; new fare is {offer.currency} "
                    f"{new_paise / 100:.2f}."
                ),
                previous_total_paise=prev_paise,
                new_total_paise=new_paise,
            )

        if "TIMEOUT" in ref or simulate in ("timeout", "supplier_timeout"):
            # FIX-P21-05: map to BookingFailureReason.supplier_timeout
            raise InventoryRevalidateError(
                "supplier_timeout",
                "Supplier timed out while revalidating this offer.",
            )

        offer.is_revalidated = True
        offer.valid_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        return offer

    async def book(self, offer: NormalizedOffer, passengers: List[Dict[str, Any]]):
        from app.schemas.booking_result import BookResult

        pnr = f"MOCK-PNR-{str(uuid.uuid4())[:8].upper()}"
        return BookResult(
            pnr=pnr,
            supplier_booking_id=f"MOCK-BID-{str(uuid.uuid4())[:8].upper()}",
            ticket_numbers=[f"MOCK-TKT-{str(uuid.uuid4())[:6].upper()}"],
            raw={"provider": self.supplier_code, "inventory_mode": "mock"},
        )

    async def cancel(self, booking_ref: str) -> bool:
        return True

    async def status(self, booking_ref: str) -> Dict[str, Any]:
        return {
            "status": "confirmed" if booking_ref.startswith("MOCK-PNR-") else "unknown",
            "supplier_ref": booking_ref,
            "raw": {"provider": self.supplier_code},
        }

    def map_error(self, exc: Exception) -> InventoryRevalidateError:
        mapped = super().map_error(exc)
        # Mock could specialize vendor strings here later
        return mapped
