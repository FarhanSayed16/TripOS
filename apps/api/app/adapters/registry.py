from typing import Dict, Type
from app.adapters.base import BaseAdapter
from app.adapters.mock_adapter import MockAdapter


class AdapterRegistry:
    """
    Singleton registry to resolve supplier codes to their adapter instances.
    """
    
    _adapters: Dict[str, BaseAdapter] = {}

    @classmethod
    def register(cls, adapter_class: Type[BaseAdapter]):
        """Register an adapter class. Instantiates it and maps it by supplier_code."""
        instance = adapter_class()
        cls._adapters[instance.supplier_code] = instance

    @classmethod
    def get_adapter(cls, supplier_code: str) -> BaseAdapter:
        """Retrieve an adapter by supplier code."""
        adapter = cls._adapters.get(supplier_code)
        if not adapter:
            raise ValueError(f"No adapter registered for supplier code: {supplier_code}")
        return adapter


from app.adapters.tbo_adapter import TboAdapter

# Initialize registry with adapters
AdapterRegistry.register(MockAdapter)
AdapterRegistry.register(TboAdapter)
