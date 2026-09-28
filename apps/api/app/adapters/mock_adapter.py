import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from app.schemas.inventory import (
    SearchQuery,
    NormalizedOffer,
    AdapterCapabilities,
    InventoryType,
    BaggageInfo,
    FlightSegment,
)
from app.adapters.base import BaseAdapter
from app.core.inventory_errors import InventoryRevalidateError
from app.schemas.ancillaries import (
    AncillaryCatalog,
    AncillaryOption,
    SeatMapResponse,
    SeatRow,
    SeatCell,
)


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
            can_ancillaries=True,
            can_seat_map=True,
        )

    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        offers = []
        deal = (query.deal_code or "").strip().upper() or None
        if not deal and query.deal_codes:
            deal = str(query.deal_codes[0]).strip().upper() or None
        # Corporate/promo codes get a small mock discount on family fares
        deal_discount = 0.05 if deal else 0.0

        def _seg(
            *,
            marketing: str,
            operating: str,
            flight: str,
            dep: str,
            arr: str,
            duration: int,
        ) -> FlightSegment:
            return FlightSegment(
                origin=query.origin.upper(),
                destination=query.destination.upper(),
                departure_at=dep,
                arrival_at=arr,
                marketing_carrier=marketing,
                operating_carrier=operating,
                flight_number=flight,
                duration_minutes=duration,
                cabin="economy",
            )

        if query.type == InventoryType.FLIGHT:
            family_group = f"MOCK-FG-{query.origin}-{query.destination}-MK101"
            # FC Phase 6 — branded fare family variants (same flight)
            for family, code, total, checked, desc in [
                ("Basic", "BASIC", 12000.0, 0, "Basic — cabin bag only, no changes."),
                ("Flex", "FLEX", 15000.0, 15, "Flex — 15kg checked, free date change."),
                ("Premium", "PREMIUM", 18500.0, 30, "Premium — 30kg + seat + meal included."),
            ]:
                priced = round(total * (1.0 - deal_discount), 2)
                base = round(priced * 0.8, 2)
                offers.append(
                    NormalizedOffer(
                        id=str(uuid.uuid4()),
                        supplier_code=self.supplier_code,
                        supplier_reference=f"MOCK-FLIGHT-001-{code}",
                        type=InventoryType.FLIGHT,
                        currency="INR",
                        total_amount=priced,
                        base_amount=base,
                        tax_amount=round(priced - base, 2),
                        title=f"MockAir {family}: {query.origin} to {query.destination}",
                        description=f"Non-stop, 2h 30m. {desc}",
                        inventory_mode="mock",
                        source_type="mock",
                        duration_minutes=150,
                        stops=0,
                        airline_code="MK",
                        airline_name="MockAir",
                        depart_time="08:00",
                        fare_family=family,
                        fare_family_code=code,
                        cabin="economy",
                        baggage=BaggageInfo(
                            cabin_kg=7,
                            checked_kg=float(checked) if checked else None,
                            notes=desc,
                        ),
                        family_group_id=family_group,
                        supports_ancillaries=True,
                        supports_seat_map=True,
                        deal_code=deal,
                        segments=[
                            _seg(
                                marketing="MK",
                                operating="AI",
                                flight="MK101",
                                dep="08:00",
                                arr="10:30",
                                duration=150,
                            )
                        ],
                        raw_data={
                            "airline": "MockAir",
                            "airline_code": "MK",
                            "flight_number": "MK101",
                            "inventory_mode": "mock",
                            "provider": "mock_supplier",
                            "fare_family": family,
                            "fare_family_code": code,
                            "family_group_id": family_group,
                            "deal_code": deal,
                            "operating_carrier": "AI",
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
                    total_amount=round(12500.0 * (1.0 - deal_discount), 2),
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
                    fare_family="Basic",
                    fare_family_code="BASIC",
                    cabin="economy",
                    baggage=BaggageInfo(cabin_kg=7, checked_kg=None, notes="Cabin only"),
                    supports_ancillaries=True,
                    supports_seat_map=False,
                    deal_code=deal,
                    segments=[
                        _seg(
                            marketing="MB",
                            operating="MB",
                            flight="MB202",
                            dep="14:30",
                            arr="16:00",
                            duration=90,
                        ),
                        FlightSegment(
                            origin="HYD",
                            destination=query.destination.upper(),
                            departure_at="17:00",
                            arrival_at="19:30",
                            marketing_carrier="MB",
                            operating_carrier="6E",
                            flight_number="MB203",
                            duration_minutes=150,
                            cabin="economy",
                        ),
                    ],
                    raw_data={
                        "airline": "MockBudget",
                        "flight_number": "MB202",
                        "inventory_mode": "mock",
                        "deal_code": deal,
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
                    fare_family="Flex",
                    fare_family_code="FLEX",
                    cabin="economy",
                    supports_ancillaries=True,
                    supports_seat_map=True,
                    segments=[
                        _seg(
                            marketing="MR",
                            operating="MR",
                            flight="MR777",
                            dep="10:15",
                            arr="13:15",
                            duration=180,
                        )
                    ],
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
                    segments=[
                        _seg(
                            marketing="MG",
                            operating="MG",
                            flight="MG404",
                            dep="19:45",
                            arr="22:25",
                            duration=160,
                        )
                    ],
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
        extras = (offer.raw_data or {}).get("selected_extras") or []
        return BookResult(
            pnr=pnr,
            supplier_booking_id=f"MOCK-BID-{str(uuid.uuid4())[:8].upper()}",
            ticket_numbers=[f"MOCK-TKT-{str(uuid.uuid4())[:6].upper()}"],
            raw={
                "provider": self.supplier_code,
                "inventory_mode": "mock",
                "fare_family": offer.fare_family,
                "selected_extras": extras,
            },
        )

    async def get_ancillaries(self, offer: NormalizedOffer) -> AncillaryCatalog:
        if offer.type != InventoryType.FLIGHT:
            return AncillaryCatalog(
                supported=False,
                message="Ancillaries only for flights in V1",
            )
        if offer.supports_ancillaries is False:
            return AncillaryCatalog(supported=False, message="Not available for this offer")
        cur = offer.currency or "INR"
        items = [
            AncillaryOption(
                code="BAG_5KG",
                type="baggage",
                label="Extra 5kg checked bag",
                description="Add 5kg to checked allowance",
                amount=750.0,
                currency=cur,
            ),
            AncillaryOption(
                code="BAG_10KG",
                type="baggage",
                label="Extra 10kg checked bag",
                amount=1200.0,
                currency=cur,
            ),
            AncillaryOption(
                code="MEAL_VEG",
                type="meal",
                label="Vegetarian meal",
                amount=350.0,
                currency=cur,
            ),
            AncillaryOption(
                code="MEAL_NONVEG",
                type="meal",
                label="Non-veg meal",
                amount=350.0,
                currency=cur,
            ),
            AncillaryOption(
                code="SSR_WCHR",
                type="ssr",
                label="Wheelchair assistance",
                description="SSR WCHR — no charge (request only)",
                amount=0.0,
                currency=cur,
                meta={"ssr_code": "WCHR"},
            ),
        ]
        return AncillaryCatalog(supported=True, currency=cur, items=items)

    async def get_seat_map(self, offer: NormalizedOffer) -> SeatMapResponse:
        if offer.type != InventoryType.FLIGHT:
            return SeatMapResponse(supported=False, message="Seat map only for flights")
        if offer.supports_seat_map is False:
            return SeatMapResponse(
                supported=False,
                message="Seat selection not available for this fare",
            )
        cur = offer.currency or "INR"
        rows: List[SeatRow] = []
        for row_num in range(10, 16):
            cells = []
            for letter, chars in [
                ("A", ["window"]),
                ("B", ["middle"]),
                ("C", ["aisle"]),
                ("D", ["aisle"]),
                ("E", ["middle"]),
                ("F", ["window"]),
            ]:
                # Block a couple of seats for realism
                available = not (row_num == 12 and letter in ("A", "F"))
                premium = row_num <= 11
                amount = 800.0 if premium else 450.0
                cells.append(
                    SeatCell(
                        seat=f"{row_num}{letter}",
                        available=available,
                        amount=amount if available else 0.0,
                        currency=cur,
                        characteristics=chars + (["exit"] if row_num == 14 else []),
                    )
                )
            rows.append(SeatRow(row=row_num, seats=cells))
        return SeatMapResponse(
            supported=True,
            currency=cur,
            cabin=offer.cabin or "economy",
            rows=rows,
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
