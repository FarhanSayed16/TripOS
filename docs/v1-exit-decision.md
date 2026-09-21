# TripOS — V1 Exit Decision

**Status:** **FIX V1 LONGER** (interim — Sprint P, 2026-09-19).  
**Not a GO V2.** Revisit after hosted smoke + commercial sign-off + pilot shortlist.

## Metrics Summary (Last 30 Days)

> Populate from `/admin/analytics` after hosted deploy + real pilot traffic.

- **Active Transacting Agents:** TBD (no hosted pilot traffic yet)
- **Total GMV:** TBD
- **Booking Failure Rate:** TBD
- **Dead Letters (Permanent Worker Failures):** TBD
- **Support Load (Qualitative):** TBD

## Go Criteria Assessment

- [x] **Core loop used without constant hand-holding?**  
  Locally: **Yes** — E2E happy path green ×2 (`docs/e2e-runs.md`). Hosted: **not proven**.
- [ ] **No critical money/booking integrity bugs open?**  
  Engineering P0s from Sprint O/P closed for mock path. Live Razorpay + hosted still open.
- [ ] **Target pilot size met (or consciously waived)?**  
  No — tracker empty pending Nilesh (`docs/pilot-onboarding-tracker.md`).

## Decision

**[ ] GO V2** **[x] FIX V1 LONGER**

**Rationale (Sprint P):** Local sandbox E2E is green, but Phase 31 GO requires hosted proof, commercial answers, and pilot size. V2/V3 scaffolding stays prototype-only until this decision flips to GO.

### Interim engineering stance

- Freeze claiming Phases 32–38 as exit-complete.
- Prefer finishing hosted smoke + Nilesh commercial/pilot over new V2 scope (Sprint Q+).
- Source of truth for 31–40 gaps: `docs/phase-31-40-audit-fixes.md`.
- Sprint P board: `docs/sprint-p-status.md`.

## Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Engineering | Farhan | 2026-09-19 | FIX V1 — E2E done; hosted/commercial/pilot open |
| Commercial | Nilesh | | |

## Next Steps

1. Farhan: deploy Render + Vercel → `hosted_smoke.py` → tick `ops/HOSTED_SMOKE.md`.
2. Nilesh: sign commercial checklist + fill pilot shortlist.
3. Re-open this file: tick GO V2 only when metrics + pilot gates are real (or consciously waived).
