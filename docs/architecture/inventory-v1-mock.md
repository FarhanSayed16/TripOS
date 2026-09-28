# Inventory V1 — mock / simulated / live honesty (FC Phase 1)

**Status:** Active — live HTTP scaffold ready; default still mock-only.  
**Related:** FIX-P21-03, FIX-P25-01, Sprint L, FC Phases 0–1.

## Supplier selection

Configured via env (not hardcoded):

```bash
INVENTORY_SUPPLIERS=mock_supplier          # default — pilot / CI
INVENTORY_SUPPLIERS=mock_supplier,tbo      # include TBO (sim or live per flag)
INVENTORY_SUPPLIERS=tbo                    # TBO only (staging live tests)
```

`apps/api/app/services/inventory.py` reads `settings.inventory_supplier_codes`.

## TBO modes (FC Phase 1)

| Mode | When | Offer title / PNR |
|---|---|---|
| **Simulated** | `TBO_LIVE_ENABLED=false` OR credentials missing | `[SIMULATED] …` / `SIM-TBO…` |
| **Live** | `TBO_LIVE_ENABLED=true` **and** base URL + client id + user + password set | Real titles / sandbox or prod PNRs |

Live client: `app/adapters/tbo_live_client.py` (httpx).  
Simulated client: `app/adapters/tbo_simulated_client.py`.  
Adapter picks mode at init and sets `NormalizedOffer.inventory_mode`.

Agent UI shows a **source badge** (`tbo · live` / `tbo · simulated` / `mock_supplier · mock`).

## Staging live enablement

1. Fill `docs/phase-0/FC_CAPABILITY_MATRIX.md` + secrets pack  
2. Set env from `docs/ops/FC_STAGING_SECRETS_CHECKLIST.md`  
3. `alembic upgrade head` (booking ticket ref columns)  
4. `SEARCH_CACHE_ENABLED=true`, vault `r2`/`s3`  
5. Smoke: `docs/ops/HOSTED_SMOKE.md` § FC Phase 1  

**Do not** set `TBO_LIVE_ENABLED=true` in production without Sahil sandbox→prod gate.

## Contract

Adapters implement `BaseAdapter`: `search`, `revalidate`, `book` → `BookResult`, `cancel`, `status`, `map_error`.

Pytest: `tests/test_adapters_contract.py`, `tests/test_fc_phase1_live_spine.py`.
