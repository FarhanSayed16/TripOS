"""Config-driven supplier selection (Sprint R: strategies match runtime)."""
from __future__ import annotations

from typing import List

from app.adapters.registry import AdapterRegistry
from app.core.config import settings
from app.schemas.inventory import NormalizedOffer, SearchQuery


class SupplierStrategy:
    """Config-driven supplier selection."""

    @classmethod
    def get_strategy(cls) -> str:
        return (getattr(settings, "SUPPLIER_STRATEGY", "all") or "all").lower()

    async def select_for_search(self, query: SearchQuery) -> List[str]:
        """Returns ordered list of supplier_codes to search."""
        configured = list(settings.inventory_supplier_codes)
        active = [c for c in configured if c in AdapterRegistry._adapters]
        strategy = self.get_strategy()
        if strategy == "primary_only":
            return active[:1]
        # failover + all: return full ordered list; inventory.py executes differently
        return active

    async def select_for_book(self, offer: NormalizedOffer) -> str:
        return offer.supplier_code
