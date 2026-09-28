# FC Phase 3 — Single-supplier pilot waiver

**Date:** 2026-09-28  
**Status:** Active until TripJack (or second live feed) is wired  

## Decision

TripOS pilot runs with **one primary live supplier: TBO** (pending Sahil credentials).  
A second **live** adapter is **waived** for FC Phase 3 exit.

## How aggregation is still tested

| Mode | How |
|---|---|
| Multi-source concat + dedupe | Set `INVENTORY_SUPPLIERS=mock_supplier,tbo` — mock + TBO (sim or live) exercise merge |
| Prefer cheapest / preferred supplier | `offer_aggregation.dedupe_offers` prefers `tbo` over `mock_supplier` on price ties |
| Failover | `SUPPLIER_STRATEGY=failover` still supported |

## When this waiver ends

- Nilesh/Sahil deliver TripJack (or second feed) sandbox, **or**  
- Commercial requires dual-live aggregation for pilot agents  

Then: implement `tripjack_adapter.py`, remove this waiver, re-run Phase 3 acceptance with two live codes.

## Sign-off

| Role | Name | Date |
|---|---|---|
| Engineering | Farhan | 2026-09-28 |
| Commercial | Nilesh | _pending_ |
