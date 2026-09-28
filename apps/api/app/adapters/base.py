from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from app.schemas.inventory import SearchQuery, NormalizedOffer, AdapterCapabilities
from app.schemas.booking_result import BookResult
from app.core.inventory_errors import InventoryRevalidateError


class BaseAdapter(ABC):
    """
    Abstract base class for all travel inventory suppliers (flights, hotels).
    """

    @property
    @abstractmethod
    def supplier_code(self) -> str:
        """Unique identifier (e.g. 'mock_supplier', 'tbo')."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        pass

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[NormalizedOffer]:
        pass

    @abstractmethod
    async def revalidate(self, offer: NormalizedOffer) -> NormalizedOffer:
        """
        Recheck price/availability. May raise InventoryRevalidateError
        with codes: fare_changed | sold_out | supplier_timeout | supplier_error.
        """
        pass

    @abstractmethod
    async def book(
        self, offer: NormalizedOffer, passengers: List[Dict[str, Any]]
    ) -> Union[BookResult, str]:
        """
        Book offer. Prefer BookResult (PNR + ticket refs); str PNR still accepted.
        """
        pass

    @abstractmethod
    async def cancel(self, booking_ref: str) -> bool:
        pass

    @abstractmethod
    async def status(self, booking_ref: str) -> Dict[str, Any]:
        """
        Fetch supplier booking/order status.
        Normalized shape: { "status": str, "supplier_ref": str, "raw": dict }
        """
        pass

    def map_error(self, exc: Exception) -> InventoryRevalidateError:
        """
        Map vendor-specific exceptions to TripOS InventoryRevalidateError.
        Override per adapter; default wraps as supplier_error.
        """
        if isinstance(exc, InventoryRevalidateError):
            return exc
        return InventoryRevalidateError(
            "supplier_error",
            str(exc) or "Supplier error",
        )
