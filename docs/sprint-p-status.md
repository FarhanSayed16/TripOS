# Sprint P — Close V1 leftovers (status board)

**Date:** 2026-09-19  
**Goal:** Honest Phase 31 GO/FIX after E2E + hosted + commercial + pilot gates.  
**Engineering owner:** Farhan · **Commercial / pilot:** Nilesh · **Supplier sandbox:** Sahil

## Board

| Gate | Owner | Status | Evidence |
|---|---|---|---|
| E2E green ×2 | Farhan | **DONE** | `docs/e2e-runs.md` — 15/15 ×2 |
| Hosted smoke (Render + Vercel) | Farhan | **BLOCKED** — no deploy URLs/secrets | Run `python scripts/hosted_smoke.py` when `TRIPOS_API_URL` exists; checklist `ops/HOSTED_SMOKE.md` |
| Commercial checklist signed | Nilesh | **PENDING** | `phase-0/COMMERCIAL_CHECKLIST.md` — or write “Accept Farhan pilot defaults” |
| Pilot shortlist (≥5 rows) | Nilesh | **PENDING** | `pilot-onboarding-tracker.md` |
| ≥3 real paid bookings | Nilesh + Farhan | **PENDING** | Blocked on hosted + Razorpay test |
| Phase 31 decision | Founders | **FIX V1** interim | `docs/v1-exit-decision.md` |

## What Sprint P shipped (engineering)

1. Unblocked local E2E (Postgres + Windows loop + phone + quote `booking` load + outbox enum + confirm commercial failures).
2. Hosted smoke script + honest blocker doc.
3. Phase 31 recorded as **FIX V1 longer** until hosted/commercial/pilot close.
4. Pytest `tests/test_sprint_p.py` for gate honesty.

## Nilesh — minimum to unlock GO V2

1. Sign commercial checklist (or explicitly accept pilot defaults).
2. Fill 5–10 real agencies in the pilot tracker.
3. After Farhan completes hosted smoke: schedule demos from `pilot-demo-script.md`.

## Farhan — next when accounts exist

1. Render Blueprint from `render.yaml` + Vercel `apps/web`.
2. Fill gitignored `secrets/04-hosting-accounts.md`.
3. `TRIPOS_API_URL=... TRIPOS_WEB_URL=... python scripts/hosted_smoke.py`
4. Tick `ops/HOSTED_SMOKE.md` and flip Phase 31 to GO when metrics + pilot size allow.

## Honest claim

Sprint P **engineering** exit is closed for E2E. Sprint P **product** exit (hosted + commercial + pilot) remains open — do **not** claim Phase 31 GO.
