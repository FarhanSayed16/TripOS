# Multi-supplier honesty (FIX-P36-01 / P36-02)

**Sprint R — 2026-09-19**

## Strategies (runtime matches config)

| `SUPPLIER_STRATEGY` | Behavior |
|---|---|
| `all` | Parallel fan-out across configured, CB-closed suppliers |
| `primary_only` | Only first code in `INVENTORY_SUPPLIERS` |
| `failover` | **Sequential**; stop after first supplier that returns ≥1 offer |

## TBO

`tbo` / `mock_tbo` adapters are **SIMULATED**. Do not present as live sandbox until Sahil credentials + real httpx client.

Default: `INVENTORY_SUPPLIERS=mock_supplier`.

## Booking.supplier_code

Persisted on confirm/fail (Sprint R migration `a2b3c4d5e6f7`). Taken from offer snapshot `supplier_code`.

## Kill switch

Admin `POST /admin/suppliers/{code}/toggle` sets circuit-breaker manual override. Staging proof = toggle primary off → search still returns mock (or empty if only one supplier).
