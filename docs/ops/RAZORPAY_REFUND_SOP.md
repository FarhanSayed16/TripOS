# Ops: Manual Razorpay refund (V1)

**Policy:** TripOS V1 does **not** auto-refund. Agents/admins process refunds in the Razorpay Dashboard, then optionally note the outcome in quote audit / CRM.

## When to refund

- Booking `failed` after payment captured (see `PAYMENT_CAPTURED_BOOKING_FAILED.md`)
- Customer cancel before supplier confirm (if commercially agreed)
- Duplicate capture / amount mismatch (rare — investigate first)

## Steps (Razorpay Dashboard)

1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com/) (test or live mode matching `PAYMENTS_MODE`).
2. Go to **Payments** → find payment by `gateway_payment_id` / order id from TripOS quote payment row.
3. Open payment → **Refund** → full or partial amount (paise/INR as shown).
4. Copy Razorpay refund id.
5. In TripOS: open quote → confirm failure banner / audit; contact customer on WhatsApp with refund id.
6. Optional later: admin stub creating a `Refund` DB row (not required for pilot).

## What UI must not imply

- No “Refund” button that claims TripOS completed a gateway refund
- Failures page copy already states refunds are manual in Razorpay

## Partial refunds

Prefer full refund + new quote for V1 simplicity unless Nilesh documents otherwise.
