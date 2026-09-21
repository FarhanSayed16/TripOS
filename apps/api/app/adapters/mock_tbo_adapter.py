import asyncio
import uuid
import random
from typing import List

from app.adapters.base import BaseAdapter
from app.schemas.inventory import SearchQuery, NormalizedOffer, Price
from app.core.config import settings
from app.core.inventory_errors import InventoryRevalidateError

class MockTboAdapter(BaseAdapter):
    """
    A second mock adapter representing another supplier (e.g., TBO or TripJack).
    Used to test multi-supplier strategy and failover.
    """
    
    @property
    def supplier_code(self) -> str:
        return "mock_tbo"

    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        if settings.MOCK_SUPPLIER_LATENCY_MS > 0:
            await asyncio.sleep(settings.MOCK_SUPPLIER_LATENCY_MS / 1000.0)

        # Fail randomly if configured
        if random.random() < settings.MOCK_SUPPLIER_FAIL_RATE:
            raise InventoryRevalidateError("tbo_timeout", "TBO mock timeout")

        if query.type != "flight":
            return []

        # Return slightly different offers to distinguish from primary mock
        offers = [
            NormalizedOffer(
                id=f"tbo_fl_{uuid.uuid4().hex[:8]}",
                supplier_id=self.supplier_code,
                title=f"TBO Air: {query.origin} to {query.destination}",
                description="Economy (TBO Exclusive)",
                price=Price(total_amount=random.randint(400000, 1500000), currency="INR"),
            ),
            NormalizedOffer(
                id=f"tbo_fl_{uuid.uuid4().hex[:8]}",
                supplier_id=self.supplier_code,
                title=f"TBO Premium: {query.origin} to {query.destination}",
                description="Business (TBO Exclusive)",
                price=Price(total_amount=random.randint(1800000, 4500000), currency="INR"),
            ),
        ]
        return offers

    async def revalidate(self, offer: NormalizedOffer) -> NormalizedOffer:
        if settings.MOCK_SUPPLIER_LATENCY_MS > 0:
            await asyncio.sleep(settings.MOCK_SUPPLIER_LATENCY_MS / 1000.0)

        if random.random() < settings.MOCK_SUPPLIER_FAIL_RATE:
            raise InventoryRevalidateError("tbo_fare_changed", "TBO Fare increased")
            
        return offer

    async def book(self, offer: NormalizedOffer, passengers: List[dict]) -> str:
        if settings.MOCK_SUPPLIER_LATENCY_MS > 0:
            await asyncio.sleep(settings.MOCK_SUPPLIER_LATENCY_MS / 1000.0)
            
        if random.random() < settings.MOCK_SUPPLIER_FAIL_RATE:
            raise InventoryRevalidateError("tbo_book_failed", "TBO booking failed")
            
        return f"TBO{uuid.uuid4().hex[:6].upper()}"

    async def cancel(self, supplier_pnr: str) -> bool:
        return True

    async def status(self, supplier_pnr: str) -> str:
        return "confirmed"
