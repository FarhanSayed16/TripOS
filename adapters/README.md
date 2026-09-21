# Supplier adapters

**Canonical code:** [`apps/api/app/adapters/`](../apps/api/app/adapters/)

| File | Role |
|---|---|
| `base.py` | `BaseAdapter` ABC (`search`, `revalidate`, `book`, `cancel`, `status`, `map_error`) |
| `mock_adapter.py` | Deterministic mock flights/hotels |
| `registry.py` | In-process registry (`mock_supplier`) |

This top-level `adapters/` directory is reserved for a future extract (shared package / multi-service). Until then, implement and test adapters under `apps/api/app/adapters/` only.

Contract tests: `apps/api/tests/test_adapters_contract.py`
