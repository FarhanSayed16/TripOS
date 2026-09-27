# Inventory V1 — mock-only suppliers (Sprint L honesty)

**Status:** Active until real sandbox HTTP + credentials (Phase 25 exit).  
**Related:** FIX-P21-03, FIX-P25-01, Sprint L.

## Supplier selection

Configured via env (not hardcoded):

```bash
INVENTORY_SUPPLIERS=mock_supplier          # default — pilot / CI
INVENTORY_SUPPLIERS=mock_supplier,tbo      # optional: include SIMULATED TBO
```

`apps/api/app/services/inventory.py` reads `settings.inventory_supplier_codes`.

TBO adapter remains **registered** for revalidate/book of any historical `tbo` offers, but:

- Search does **not** include TBO unless listed in `INVENTORY_SUPPLIERS`
- Simulated offers are titled `[SIMULATED] …`
- Simulated PNRs are prefixed `SIM-TBO…`

`Supplier` / `SupplierConfig` DB models exist for later live wiring; do not treat them as live until Fernet/KMS encryption and real httpx clients ship.

Canonical adapter code: **`apps/api/app/adapters/`**.

## Search cache (Redis / Upstash)

**V1 mock pilot:** cache optional (mock has no L2B contract).  
**Live suppliers:** required — see **`architecture/look-to-book-search-cache-plan.md`** (phased L2B + shopping cache).  
Rate limit remains 30 searches/min/org (TripOS protection); L2B metering is separate.

## Contract

Adapters must implement `BaseAdapter`: `search`, `revalidate`, `book`, `cancel`, `status`, `map_error`.

Pytest: `apps/api/tests/test_adapters_contract.py`, `tests/test_sprint_l.py`.
