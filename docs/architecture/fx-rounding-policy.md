# FX rounding policy (FC Phase 4)

**Scope:** Display currency conversion only. Supplier fares and Razorpay charge amounts stay in settle currency (`CHARGE_CURRENCY`, default **INR**).

## Rules

1. **Never mutate supplier fare** — `NormalizedOffer.total_amount` / `currency` are charge-side. FX writes only to the `money` envelope (`display_currency`, `display_amount`, `fx_rate`, `fx_as_of`).
2. **Rate meaning** — `fx_rates.rate` = units of **quote** currency per **1 unit** of **base** (usually INR). Example: `INR→USD rate=0.012` means ₹1 ≈ $0.012.
3. **Rounding** — Commercial **ROUND_HALF_UP** to **2 decimal places** on display major units (`app.services.fx.round_money`). Intermediate rates may use 8 decimal places.
4. **Quote snapshot** — On create, quote stores `charge_currency`, `display_currency`, `fx_rate`, `fx_as_of`, `fx_source`. Public/share text uses the snapshot, not a live re-fetch.
5. **Payments** — Create payment link / webhook still validate **INR** (or configured charge currency). Display FX must not change gateway amount.
6. **Missing rate** — Search falls back to charge currency (warning log). Quote create returns `FX_RATE_MISSING` if org prefers a currency with no active rate.
7. **Provider pull** — `FX_PROVIDER_ENABLED=false` by default; admin manual CRUD + seed endpoint are the bootstrap path.

## Ops

- Admin UI: `/admin/fx`
- Seed demo pairs: `POST /api/v1/admin/fx-rates/seed`
- Org setting: `preferred_currency` via `PATCH /api/v1/organizations/me`
- User override: `PATCH /api/v1/auth/me` `{ "preferred_currency": "USD" }`
