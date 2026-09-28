# FC Phase 1 — Idempotency audit (pay + book)

**Date:** 2026-09-28  
**Scope:** Prevent double Payment Links and double PNRs under retries.

## Payment link create

| Check | Status | Evidence |
|---|---|---|
| Idempotency key claimed before create | **OK** | `payments.create_payment_for_quote` → `claim_idempotency_key(..., "create_payment_link")` |
| Key scoped to quote | **OK** | Key derived from quote id path |
| Offline pay separate key | **OK** | `offline_pay_{quote.id}` |

## Booking confirm (worker)

| Check | Status | Evidence |
|---|---|---|
| Skip if already `confirmed` | **OK** | `handle_booking_confirm` early return + log `booking_confirm_idempotent_skip` |
| Outbox `FOR UPDATE SKIP LOCKED` | **OK** | Worker claim pattern (existing) |
| Commercial failures not infinite-retried | **OK** | fare_changed / sold_out → failed Booking, job done |
| Transient errors retry | **OK** | Exception re-raised for worker backoff |

## Gaps / follow-ups

| Item | Priority | Notes |
|---|---|---|
| Supplier-side idempotency key on Book | P1 | Pass TripOS quote/booking id if TBO supports ClientReference |
| Compensating cancel on multi-item partial book | P2 | Deferred (V1 one item per quote) |
| Webhook duplicate `payment_link.paid` | OK if outbox unique per quote | Confirm one confirm job per payment |

## Verdict

**Safe for single-item V1 pilot.** Re-audit when multi-item quotes or live TBO ClientReference fields are wired.
