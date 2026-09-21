# Ops: Payment captured but booking failed

**Audience:** Farhan (ops) / agency admins during pilot.  
**UI:** Agent home attention strip, quote detail, `/admin/failures`.  
**Related:** `docs/failure-taxonomy.md`, Sprint K Failures UI, Sprint J confirm exhaust.

## Immediate triage

1. Open **Admin → Failures** (dead-letter jobs + failed bookings) or agent **Home**.
2. Open the quote (`/app/quotes/{id}` or public `/q/{token}`).
3. Confirm payment is **captured** in TripOS and Razorpay Dashboard.
4. Read `booking.failure_reason` / audit actions (`booking.failed_*`).

**Do not auto-refund in TripOS.** Process refunds manually in Razorpay (see `RAZORPAY_REFUND_SOP.md`).

## Playbook by `failure_reason`

| Reason | Meaning | Action |
|---|---|---|
| `fare_changed` | Supplier fare moved after pay | Refund difference or full; re-quote customer with refresh |
| `sold_out` | Inventory gone | Full refund; search again |
| `supplier_timeout` | Vendor timed out / job dead | Check dead-letter job; retry offline rebook if seats exist, else refund |
| `supplier_error` | Vendor fault | Escalate to supplier; refund if cannot recover |
| `missing_pax` | Quote paid without usable pax | Collect pax + rebook manually or refund |
| `unknown` | Catch-all | Inspect audit + dead-letter stack; refund if stuck |

## Dead-letter jobs

When `booking_confirm` hits max retries:

- Job status = `dead` (`JobStatus.dead`)
- Booking upserted `failed` + `supplier_timeout`
- `manual_refund_review` job may be enqueued
- Sentry message `job_dead:booking_confirm` if `SENTRY_DSN` set

Inspect payload `quote_id` / `payment_id` on `/admin/failures` → Dead-letter jobs tab.

## Escalation

- **Engineering:** stack in `error_details`, Sentry event, worker logs
- **Commercial:** Nilesh if refund policy / agency credit disputed
