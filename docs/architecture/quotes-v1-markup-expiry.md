# Quotes V1 — markup & expiry honesty

**Related:** AUDIT-012, AUDIT-013, FIX-P11-16

## Markup

- Agent markup is **flat ₹ stored as paise** on `quote_items.agent_markup`.
- **% markup is not implemented** in V1 (master plan wording updated).
- `platform_fee` remains `0` until Phase 0 commercial answers land.

## Quote expiry

- Defaults: **4h flights / 12h hotels** from creation (`services/quotes.py`).
- Agent **extend ≤24h with fare-risk warning** is **not implemented**.
- Do not treat master-plan extend checkbox as done until an API + UI ships.

## Revalidate vs expiry

- Payment link creation still revalidates offers even if within `valid_until`.
- Expired quotes cannot create payment links (`QUOTE_EXPIRED`).
