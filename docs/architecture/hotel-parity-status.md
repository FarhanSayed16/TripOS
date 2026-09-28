# Hotel inventory parity status (FC Phase 3)

**Date:** 2026-09-28  
**Status:** **Mock-gated** — shared search stack; no live hotel supplier yet  

## What works today (same path as flights)

| Concern | Status |
|---|---|
| `POST /inventory/search/hotels` | Yes → `search_inventory` |
| Redis shopping cache (keyed by type) | Yes when `SEARCH_CACHE_ENABLED` |
| L2B metering on live miss | Yes |
| Revalidate before pay/book | Yes (mock sold-out fixture) |
| Agent hotel search UI | Yes |
| Dedupe / sort / filter pipeline | Yes (hotel fingerprint by hotel_id/title) |

## What does **not** work yet

| Concern | Status |
|---|---|
| Live TBO/TripJack hotel search | **No** — TBO adapter returns `[]` for non-flight |
| Hotel ancillaries / room boards | **No** |
| Hotel-specific fare rules | Derived only if present in raw |

## Gate

Until a hotel-capable live supplier is confirmed in `FC_CAPABILITY_MATRIX.md`:

- Keep `mock_supplier` in `INVENTORY_SUPPLIERS` for hotel demos, **or**  
- Accept empty hotel results when only `tbo` is configured  

Do **not** label mock hotels as live.

## Next (later phase)

Wire hotel search on primary supplier when contract includes hotels; reuse cache + L2B + aggregation unchanged.
