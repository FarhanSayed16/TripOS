# Wallet / commission formula (FIX-P33-01)

## Money columns (do not conflate)

| Field | Meaning |
|---|---|
| `supplier_cost` | What supplier charges (paise) |
| `agent_markup` | Agent margin on top of supplier |
| `platform_fee` | Platform fee (`PLATFORM_FEE_PAISE`) — **not** agent wallet |
| `customer_total` | supplier_cost + agent_markup + platform_fee |

## Commission

```
commission = f(agent_markup) via CommissionRule
  percentage → agent_markup * value / 100
  flat_paise → value
  no rule    → 100% of agent_markup
```

Ledger never inverts from `customer_total`.

## Hierarchy split (FIX-P38-01)

When booking org has `parent_organization_id`:

```
master_share = commission * MASTER_COMMISSION_OVERRIDE_BPS / 10000
sub_share    = commission - master_share
```

Default BPS = **2000** (20%). Configurable via env — not hardcoded 0.20.

## Lifecycle

`pending` → (settlement window) → `available` → `commission_paid` / settled.

Reconcile proof: `tests/test_sprint_qrst.py::test_wallet_reconcile_*`.
