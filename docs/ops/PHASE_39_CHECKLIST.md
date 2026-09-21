# Phase 39 — Ops on-call checklist (FIX-P39-01)

**Owner:** Farhan · **Link hub:** `docs/ops/`

## Daily / when paging

- [ ] Admin → Failures: dead-letter jobs + failed bookings
- [ ] Sentry: new issues on API / worker
- [ ] Render: API + worker healthy; Postgres storage
- [ ] Webhooks: Razorpay failures (if live)

## Metrics (minimum)

| Signal | Where |
|---|---|
| Booking confirm success / fail | Admin Failures + `audit_events` |
| Dead-letter spike | `jobs_outbox` status=dead + Failures UI |
| Webhook errors | Sentry + payments logs |
| Search rate-limit 429 | structlog `rate_limit_exceeded` |

## Search cache

**Decision (Sprint T):** still **skipped** for V1/V2 pilot — freshness > cache. Revisit if supplier latency becomes a cost issue.

## Worker concurrency

- Outbox uses `FOR UPDATE SKIP LOCKED` — safe for multiple worker instances.
- In-memory rate limit + circuit breaker are **per process** (OK for single instance; Redis reserved later).

## Backup restore

See `BACKUP_RESTORE.md` — local dry-run recorded Sprint T.
