# Phase 39 — Ops on-call checklist (FIX-P39-01)

**Owner:** Farhan · **Link hub:** `docs/ops/`

## Daily / when paging

- [ ] Admin → Failures: dead-letter jobs + failed bookings
- [ ] Sentry: new issues on API / worker
- [ ] Render: API + worker healthy; Postgres storage
- [ ] Webhooks: Razorpay failures (if live)

## Search cache

**Live suppliers:** follow `architecture/look-to-book-search-cache-plan.md` + `architecture/live-inventory-readiness-plan.md` Phases 2 + 5 + **7**.

| Flag | Effect |
|---|---|
| `SEARCH_CACHE_ENABLED=true` | Browse hits Redis; miss → live + set |
| `SEARCH_CACHE_REFRESH_ENABLED=true` | Worker refreshes top-N hot routes on an interval |
| `SEARCH_CACHE_REFRESH_ENABLED=false` | **Pause background refresher** (ops kill switch) |
| `L2B_SURVIVAL_*` | Auto soft-brakes when platform L2B critical — see `L2B_SURVIVAL_RUNBOOK.md` |

**Pause refresher (ops):** set `SEARCH_CACHE_REFRESH_ENABLED=false` on the worker and restart (or redeploy). User browse cache still works if `SEARCH_CACHE_ENABLED=true`.

**L2B survival (auto):** when platform L2B is critical, TTL widens (×2, cap 15m) and warm refresh pauses. Admin red banner + Sentry. Full playbook: [`L2B_SURVIVAL_RUNBOOK.md`](./L2B_SURVIVAL_RUNBOOK.md).

**Manual refresh:** enqueue outbox job `type=inventory_cache_refresh` (optional payload: `top_n`, `hot_n`, `days`).

Mock pilot may run without cache; do not skip cache once real TBO/TripJack traffic starts.

## Metrics (minimum)

| Signal | Where |
|---|---|
| Booking confirm success / fail | Admin Failures + `audit_events` |
| Dead-letter spike | `jobs_outbox` status=dead + Failures UI |
| Webhook errors | Sentry + payments logs |
| Search rate-limit 429 | structlog `rate_limit_exceeded` |
| Platform L2B / survival | Admin banner + Analytics + `GET /admin/l2b/survival` |


## Worker concurrency

- Outbox uses `FOR UPDATE SKIP LOCKED` — safe for multiple worker instances.
- In-memory rate limit + circuit breaker are **per process** (OK for single instance; Redis reserved later).

## Backup restore

See `BACKUP_RESTORE.md` — local dry-run recorded Sprint T.
