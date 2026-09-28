# Refund Runbook (FC Phase 2)

## Overview

When payment is **captured** but the booking fails or is cancelled, money must be returned.  
TripOS tracks refund **status** in-product; the Razorpay (or gateway) money movement remains an ops action until auto-refund is approved.

## Status lifecycle

| Status | Meaning |
|---|---|
| `requested` | Opened in TripOS (auto on cancel-after-capture, or ops) |
| `processing` | Ops started gateway refund |
| `succeeded` | Gateway refund done; `gateway_refund_id` stored |
| `failed` | Gateway refund failed / abandoned |

## Where to look

1. **Admin → Failures → Refunds** — queue + mark status  
2. **Agent quote detail** — refund cards for that quote  
3. **API:** `GET /admin/refunds`, `POST /admin/refunds/{id}/status`  
4. Audit actions: `refund.requested`, `refund.processing`, `refund.succeeded`, `refund.failed`

## Procedure (captured payment + failed / cancelled booking)

1. Confirm payment status = `captured` and booking `failed` or `cancelled`.
2. Open **Failures → Refunds** (or create via cancel flow which auto-requests).
3. In Razorpay Dashboard, refund using `gateway_payment_id` on the Payment.
4. In TripOS, mark refund **Processing** then **Succeeded**; paste Razorpay refund id when prompted.
5. If gateway refund fails, mark **Failed** and escalate.

## Auto request

Cancelling a quote/booking after captured payment calls `maybe_request_refund_on_cancel` → creates `requested` refund if none open.

## Related

- `docs/ops/RAZORPAY_REFUND_SOP.md`
- `docs/ops/PAYMENT_CAPTURED_BOOKING_FAILED.md`
- FC plan Phase 2 — `docs/architecture/flight-commerce-implementation-plan.md`
