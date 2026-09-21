# Booking failure taxonomy (FIX-P23-01)

TripOS maps supplier / job failures onto `BookingFailureReason` and audit actions.

## Enum → agent copy

| `BookingFailureReason` | Plan-style code | Agent meaning |
|---|---|---|
| `fare_changed` | `booking_failed_fare_changed` | Fare moved after pay — refund or re-quote |
| `sold_out` | `booking_failed_sold_out` | Inventory gone — refund or rebook elsewhere |
| `supplier_timeout` | `booking_failed_supplier_timeout` | Retryable; worker may exhaust → dead letter |
| `supplier_error` | `booking_failed_supplier_error` | Vendor fault — manual support |
| `missing_pax` | (pax gate) | Cannot book without passengers |
| `unknown` | — | Catch-all — manual review |

## `needs_manual_support`

Not a separate DB column in V1. Derived when:

- `Booking.status == failed`, **or**
- Audit / outbox payload includes `"needs_manual_support": true` (confirm exhaust, missing pax, commercial revalidate fail)

UI shows human labels via `failure_label` on booking list responses and `apps/web/src/lib/failureLabels.ts`.

## Quote page = booking detail

There is no dedicated `/app/bookings/[id]` route. Agents open **`/app/quotes/{quote_id}`** for PNR, failure banners, audit timeline, and cancel.
