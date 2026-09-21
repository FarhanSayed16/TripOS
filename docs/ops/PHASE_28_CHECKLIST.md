# Phase 28 — Reliability gate checklist (Sprint M)

Sign after Sprint K dead-letters + this Sprint M ops pack are in place.  
Hosted smoke (Phase 27 exit) can be signed separately when Render/Vercel are live.

| # | Gate | Status | Notes |
|---|---|---|---|
| 1 | Dead-letters API (`JobStatus.dead` + `error_details`) | **Done** (Sprint K) | `/api/v1/admin/dead-letters` |
| 2 | Admin Failures UI | **Done** (Sprint K) | `/admin/failures` |
| 3 | Ops runbook: pay captured / book failed | **Done** | `docs/ops/PAYMENT_CAPTURED_BOOKING_FAILED.md` |
| 4 | Manual Razorpay refund SOP | **Done** | `docs/ops/RAZORPAY_REFUND_SOP.md` |
| 5 | Backup / restore documented | **Done** | `docs/ops/RENDER_RUNBOOK.md` §4 |
| 6 | Backup restore dry-run | **Deferred ≤1 week after first hosted deploy** | Owner: Farhan — schedule after Render Postgres live |
| 7 | Multi-instance rate-limit note | **Done** | In-memory limiter; Redis provisioned but unused (see runbook). Acceptable for single-instance pilot. |
| 8 | Sentry DSN + alerts configured | **Pending secrets** | Code wired; set `SENTRY_DSN` on API+worker; smoke `/api/v1/admin/sentry-debug` |
| 9 | Hosted health smoke | **Pending deploy** | `GET /health`, `GET /ready` |

## Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Engineering | Farhan | | _sign when rows 1–5 + 7 accepted_ |
| Commercial | Nilesh | | _sign refund SOP + pilot refund policy_ |

**Phase 28 is not “exit complete” until hosted smoke (#8–9) and commercial sign-off.**
