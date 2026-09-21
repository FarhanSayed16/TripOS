# TripOS — Phase 21→30 Audit & Required Fixes

**Audit date:** 2026-09-18  
**Claimed status:** Development complete through Phase 30  
**Audit verdict:** **Not Phase-30 complete.** Phases **21–24 are substantially over-claimed** in `tripos-master-plan.md`. Phase **25 is simulated TBO, not live sandbox**. Phases **26–30** are correctly mostly unchecked but have **broken E2E**, **unproven deploy**, and **schema-drift bugs** in early Phase-30 helpers.

**Do not treat the commercial loop or pilot as trustworthy until P0/P1 below are fixed.**  
**Companion:** `docs/phase-0-20-full-audit.md` (Sprints G–I) · `docs/tripos-master-plan.md`

---

## Executive scorecard

| Phase | Master plan | Audit result | One-line |
|---|---|---|---|
| **21** Booking confirm | Mostly `[x]` | **PARTIAL** | Revalidate→book path exists; audit writes crash; retry/backoff wrong; taxonomy incomplete |
| **22** Bookings UI | Mostly `[x]` | **PARTIAL** | List exists; `bookingsApi` uses mock token; home attention missing |
| **23** Audit + failures | All `[x]` | **BROKEN / PARTIAL** | Writers use wrong `AuditEvent` columns — events do not persist |
| **24** Admin OS | Mostly `[x]` | **PARTIAL** | Overview/agents/bookings exist; Failures/Suppliers `ComingSoon`; reject/dead-letter APIs buggy |
| **25** Real supplier | 25.1 `[x]`, exit `[ ]` | **MOCK_ONLY** | `TboClient` is simulated sleep + fake JSON — exit correctly open |
| **26** Sandbox E2E | All `[ ]` | **PARTIAL / BROKEN** | Scripts exist but call obsolete APIs / wrong worker entrypoints |
| **27** Deploy | All `[ ]` | **PARTIAL** | `render.yaml` + runbooks exist; hosted smoke unproven |
| **28** Security gate | All `[ ]` | **PARTIAL** | Prior hardenings exist; dead-letter API broken; no signed gate |
| **29** Pilot | All `[ ]` | **MISSING** | Templates only — no real agents/bookings |
| **30** V1.5 friction | All `[ ]` | **PARTIAL / BUGGY** | Offline/refresh/CSV landed against nonexistent fields |

\*Honest reading: **Phases 21–25 are not exit-complete.** Phases 26–30 were never finished; claiming “done through 30” is incorrect.

---

## Finding counts (open)

| Severity | Count | Meaning |
|---|---|---|
| **CRITICAL** | 4 | Ship-blockers: cancel IDOR, AuditEvent schema, broken E2E happy path, TBO honesty |
| **HIGH** | ~18 | Confirm ops, admin bugs, bookings FE, deploy/pilot gates |
| **MEDIUM** | ~20 | Completeness / DX / scalability |
| **LOW / INFO** | ~10 | Polish / deferred |

---

# P0 — Critical blockers (fix first)

---

### FIX-P21-01 — `AuditEvent` schema drift (breaks pay / send / confirm / cancel / audit GET)

**Phases:** 21, 23  
**Severity:** CRITICAL · **Category:** bug  
**Files:** `models/commercial.py`, `services/jobs.py`, `services/payments.py`, `services/messaging.py`, `api/quotes.py`

**Problem:**  
Model columns are `entity_type`, `entity_id`, `metadata_payload`. Most writers pass `resource_type`, `resource_id`, `metadata` (or worse: `event_type`, `description`). Reader queries nonexistent `resource_*` columns.

**Impact:**  
`TypeError` on construct → webhook capture / quote send / booking confirm audits fail or leave partial state. Phase 23 exit (“what happened to this quote?”) is impossible. Money can be captured at Razorpay while TripOS fails mid-webhook.

**Required:**
- [x] Normalize **all** writers to `entity_type` / `entity_id` / `metadata_payload` (always pass `dict`, never omit)
- [x] Fix `/quotes/{id}/audit` to filter on `entity_id` + `entity_type`
- [x] Pytest: create event → read back; webhook capture still commits when audit writes

**Acceptance:** Quote audit timeline returns events after send / pay / confirm / cancel.

---

### FIX-P21-02 — Cancel quote IDOR (no org scope)

**Phase:** 21  
**Severity:** CRITICAL · **Category:** security  
**Files:** `api/quotes.py` `api_cancel_quote`

**Problem:**  
Loads `Quote.id == quote_id` only — no `organization_id` filter. Can cancel another org’s quote and trigger supplier cancel with their PNR.

**Required:**
- [x] `where(Quote.id == …, Quote.organization_id == current_user.active_organization_id)`
- [x] 404 on miss (do not leak existence)
- [x] Pytest cross-org cancel → 404

**Acceptance:** Org A cannot cancel Org B quotes.

---

### FIX-P21-03 — TBO adapter is simulated but wired as live inventory

**Phase:** 25 (blocks honest 21/26)  
**Severity:** CRITICAL · **Category:** honesty  
**Files:** `adapters/tbo_adapter.py`, `services/inventory.py`

**Problem:**  
`TboClient` docstring: “Simulated HTTP… replaced with real httpx”. Inventory hardcodes `["mock_supplier", "tbo"]`. Agents see TBO offers and `TBO*` PNRs that are not real.

**Required:**
- [x] Uncheck master plan §25.1 lifecycle / quirks `[x]` items until real sandbox HTTP + credentials
- [x] Gate TBO behind config/credentials; default mock-only for pilot demos
- [x] Label simulated PNRs clearly **or** implement real client

**Acceptance:** Either real sandbox offers **or** plan/UI honestly say “simulated”.

---

### FIX-P26-01 — E2E happy path is broken

**Phase:** 26  
**Severity:** CRITICAL · **Category:** bug / DX  
**Files:** `tests/e2e/test_e2e_happy_path.py`, other `tests/e2e/*`

**Problem:**  
Imports nonexistent `worker.process_outbox_jobs` (real: `poll_outbox` / `process_job`). Calls obsolete routes (`/mark-sent`, `/pay-link` vs `/send`, `/payment`). Revalidate E2E builds invalid Quote fields.

**Required:**
- [x] Rewrite happy path against current API + worker
- [x] Fix revalidate/failure E2E against `handle_booking_confirm`
- [x] Document how to run; optionally add CI gated job

**Acceptance:** One green happy-path E2E against local Postgres.

---

# P1 — Required to honestly close Phases 21–25

---

### FIX-P21-04 — Confirm job retry / backoff / dead-letter taxonomy

**Phase:** 21  
**Files:** `worker.py`, `services/jobs.py`

**Gaps:**
- Backoff is `2 ** attempts` **minutes**, not **30s / 2min / 10min**
- Job → `dead` does not set booking `failure_reason=supplier_timeout` + manual-support signal
- Failed booking insert vs unique `quote_id` → retry IntegrityError
- Multi-item partial book has no compensate cancel
- Docstring still says “PROTOTYPE STUB” while calling `book_offer`

**Required:**
- [x] Implement plan backoff schedule
- [x] On final failure: upsert booking `failed` + reason + audit + optional `manual_refund_review` / ops flag
- [x] Upsert booking row on retry (don’t double-insert)
- [x] Document V1 single-item quotes **or** cancel prior PNRs on partial fail
- [x] Refresh docstring

---

### FIX-P21-05 — Error-code mapping bugs (TBO / mock timeout)

**Phase:** 21 / 25  
**Files:** `tbo_adapter.py`, `mock_adapter.py`, `inventory_errors.py`

**Required:**
- [x] Fix TBO `InventoryRevalidateError` arg order `(error_code, message)`
- [x] Map mock `"timeout"` → `supplier_timeout` (enum), not `unknown`

---

### FIX-P21-06 — Offline mark-paid / JobOutbox `run_at` / Payment field drift

**Phases:** 21, 30  
**Files:** `services/payments.py` `mark_quote_paid_offline`

**Problem:** Uses nonexistent `Payment` fields (`amount_captured`, `payment_method`, `organization_id`), wrong item totals, omits required `JobOutbox.run_at`, wrong audit kwargs.

**Required:**
- [x] Align to real `Payment` / `QuoteItem.customer_total`
- [x] Always set `run_at` on outbox enqueue
- [x] Fix audit write (see FIX-P21-01)

---

### FIX-P22-01 — Bookings FE uses mock auth + localhost

**Phase:** 22  
**Files:** `apps/web/src/lib/api/bookingsApi.ts`

**Required:**
- [x] Use shared `apiSlice` / BFF + credentials (same as quotes)
- [x] Expand booking DTO with customer summary for list UI
- [x] Remove `Bearer mock-token` and hardcoded `localhost:8000`

---

### FIX-P22-02 — Home attention + booking detail incomplete

**Phase:** 22  
**Files:** `app/(agent)/app/page.tsx`, bookings routes

**Required:**
- [x] Home strip: paid/pending confirm + failed bookings (or uncheck plan)
- [x] Dedicated booking detail **or** document quote page as canonical detail and uncheck “Booking detail”

---

### FIX-P23-01 — Failure taxonomy honesty in API/UI

**Phase:** 23  

**Required:**
- [x] Document mapping: plan codes (`booking_failed_*`, `needs_manual_support`) ↔ enum `BookingFailureReason`
- [x] Persist/show `needs_manual_support` (flag or status) when confirm fails
- [x] Human-readable labels in agent UI (not raw enum only)
- [x] Uncheck master plan §23 until FIX-P21-01 works end-to-end

---

### FIX-P24-01 — Admin reject + dead-letters API bugs

**Phase:** 24 / 28  
**Files:** `api/admin.py`

**Required:**
- [x] Reject → `OrgStatus.inactive` (not `suspended`)
- [x] Dead letters → `JobStatus.dead` (not `failed`)
- [x] Response field `error_details` (not `error_msg`)
- [x] Wire `admin/failures` page (replace `ComingSoon`) **or** uncheck plan

---

### FIX-P24-02 — Admin Failures / Suppliers honesty

**Phase:** 24  

**Required:**
- [x] Build failures queue UI **or** uncheck §24 Failures `[x]`
- [x] Keep Suppliers deferred — set plan `[ ]` until Phase 36 / real supplier ops

---

### FIX-P25-01 — Real sandbox client + credential wiring + primary strategy

**Phase:** 25  

**Required:**
- [ ] Real httpx TBO (or TripJack) client with encrypted credentials from DB
- [ ] Config-driven `primary_only` supplier (stop hardcoding both mock+tbo)
- [ ] Sandbox quirks doc
- [ ] Leave §25.3 exit unchecked until live search+book proven

---

# P2 — Phases 26–30 (before claiming pilot / V1.5)

---

### FIX-P26-02 — E2E coverage + CI

- [x] Align all e2e scenarios with current routes (pax gate, expiry, tenant isolation, duplicate webhook, fare-change, rate 429)
- [x] Add search-timeout scenario
- [ ] Record two consecutive green runs (date, SHA, command) — blocked until Postgres/Docker available
- [ ] Optional: CI job with Postgres service

---

### FIX-P27-01 — Hosted deploy proof

- [x] Provision Render Blueprint + Vercel docs; fill secrets list (`JWT_SECRET`, `ENCRYPTION_KEY`, Razorpay, Resend, `FRONTEND_URL`, CORS, `SENTRY_DSN`)
- [x] Mirror worker env with API (Razorpay/Sentry/encryption) in `render.yaml`
- [ ] Hosted smoke: health + one mock or test pay loop _(pending credentials)_
- [x] Document prod URL pack path (`secrets/README.md` → copy template `04-hosting-accounts.md`)
- [x] Decide Redis: **keep provisioned, document unused by V1** (outbox is Postgres)

---

### FIX-P27-02 — Observability

- [x] Sentry init on API + worker; capture dead jobs + webhook signature failures
- [ ] Set DSNs in hosted env; configure Sentry alerts
- [ ] Smoke `/admin/sentry-debug` on hosted
- [x] Optional log drain documented (Vercel runbook)

---

### FIX-P28-01 — Reliability gate

- [x] Fix dead-letters (FIX-P24-01) + admin UI
- [x] Ops runbook: payment captured but booking failed (by `failure_reason`)
- [x] Backup restore documented; dry-run deferred ≤1 week after hosted deploy
- [x] Multi-instance rate-limit note (in-memory OK for single-instance pilot; Redis reserved)
- [ ] Signed Phase 28 checklist (Farhan + Nilesh) — template in `docs/ops/PHASE_28_CHECKLIST.md`

---

### FIX-P28-02 — Refunds honesty

- [x] Document manual Razorpay refund SOP (V1)
- [ ] Optional: admin stub creating `Refund` row
- [x] Do not imply auto-refund in UI copy (Failures page)

---

### FIX-P29-01 — Pilot onboarding (external)

- [x] Tracker + quickstart + demo script + support channel **packaged** (`docs/pilot-*.md`, `agent-quickstart.md`)
- [ ] Fill `docs/pilot-onboarding-tracker.md` with **real** agents (Nilesh)
- [ ] Publish quickstart to agents; schedule demos; create Support WhatsApp
- [ ] Exit: ≥3 agents with ≥1 real paid booking — **blocked on 27–28 + live money + Nilesh shortlist**

---

### FIX-P30-01 — Phase 30 helpers schema alignment

| Feature | Bug | Fix |
|---|---|---|
| `refresh_quote` | `QuoteStatus.superseded`, wrong item/offer fields, missing `customer_id` | **Fixed** — expire old quote; real columns; copy customer |
| CSV export | `Booking.organization_id`, `b.pnr`, wrong payment/item fields | **Fixed** (Sprint K) |
| Offline paid | See FIX-P21-06 | **Fixed** (Sprint J) |
| Bookings API | Skip `require_active_org` | **Fixed** — uses `require_active_org` |

**Also:**
- [ ] Wire FE for offline paid / CSV only if pilots need them
- [ ] Do **not** mark Phase 30 done before ranked friction from Phase 29

---

# P3 — Enhancements (optional)

| ID | Item |
|---|---|
| ENH-01 | Customer timeline bookings |
| ENH-02 | WhatsApp message presets |
| ENH-03 | Phone merge UX |
| ENH-04 | Admin booking deep-link (not only public token) |
| ENH-05 | Compensate cancel on multi-item partial book |
| ENH-06 | Next.js middleware for `/app` / `/admin` (carry-over) |

---

## What is solid (do not regress)

- Org scoping on most quote/payment/customer paths (except **cancel**)
- Customer bind on quote create; JWT `type` + `token_version`; active-org gate
- Webhook HMAC (prod) + amount verify; SKIP LOCKED + stale-running reclaim
- Public quote sanitization + opaque tokens
- Pax gate on ready + pay; revalidate-before-pay
- Platform admin guard on `/admin` APIs
- Confirm **intent** (revalidate → adapter.book) is present — needs ops/audit fixes above

---

## Master plan honesty patch (do immediately)

Uncheck or annotate until proven:

| Section | Action |
|---|---|
| §21.1 audit / backoff / needs_manual_support | Annotate PARTIAL |
| §22 booking detail / home attention | Uncheck or annotate |
| §23 all | Uncheck until AuditEvent fixed |
| §24 Failures / Suppliers | Uncheck ComingSoon pages |
| §25.1 lifecycle / quirks / strategy | Uncheck — simulated only |
| §12.2 revalidate-before-book | May be OK once confirm proven; keep tied to 21 exit |
| Claim “complete through Phase 30” | **False** — stop using that claim |

---

# Suggested fix sprints

### Sprint J — Unblock money + security (1–2 days) — **DONE**
1. FIX-P21-01 AuditEvent alignment  
2. FIX-P21-02 Cancel IDOR  
3. FIX-P21-06 Offline/outbox `run_at` + field drift  
4. FIX-P21-04 Confirm retry/upsert/taxonomy (minimum viable)  
5. FIX-P21-05 Error-code mapping  

**Exit:** Pay webhook → confirm job → audit trail works; no cross-org cancel.

### Sprint K — Agent + admin visibility (2–3 days) — **DONE**
6. FIX-P22-01 / P22-02 Bookings FE + attention  
7. FIX-P23-01 Taxonomy honesty  
8. FIX-P24-01 / P24-02 Admin dead-letters + Failures UI  
9. Master plan honesty patch  

**Exit:** Agent can see failed bookings; admin can see dead jobs.

### Sprint L — Supplier honesty + E2E (3–5 days) — **DONE** (green runs pending local Postgres)
10. FIX-P21-03 / P25-01 Gate or real TBO  
11. FIX-P26-01 / P26-02 Repair E2E + record two green runs  

**Exit:** Honest mock **or** real sandbox; repeatable E2E.  
**Note:** E2E suite rewritten; record two green runs in `docs/e2e-runs.md` once Docker Postgres is up (`docker compose up -d` → `pytest tests/e2e/`).

### Sprint M — Deploy + gate (parallel / after L) — **CODE DONE**; hosted smoke pending secrets
12. FIX-P27-* Hosted deploy + Sentry (blueprint + runbooks + captures)  
13. FIX-P28-* Reliability gate docs (sign-off pending Nilesh + hosted smoke)  
14. FIX-P30-01 Fix Phase-30 `refresh_quote` + bookings `require_active_org`  

**Exit:** Blueprint ready; ops SOPs live; refresh_quote safe. Record hosted smoke in `docs/ops/HOSTED_SMOKE.md` when credentials exist.

### Sprint N — Pilot (external) — **PACKAGED**; exit pending Nilesh + live money
15. FIX-P29-01 + Nilesh commercial (Sprint I leftovers)  

**Farhan done:** tracker, quickstart, demo script, support channel, docs index links.  
**Still open:** real agent names, demos, commercial sign-off, hosted smoke, ≥3 paid bookings.

**Then:** Rank real friction → only then call Phase 30 “done”.

---

## Checklist (copy to board)

### Sprint J
- [x] FIX-P21-01 AuditEvent writers/readers
- [x] FIX-P21-02 Cancel org scope
- [x] FIX-P21-06 Offline pay + `run_at`
- [x] FIX-P21-04 Confirm retry/upsert/dead taxonomy
- [x] FIX-P21-05 TBO/mock error codes
- [ ] Pytest: audit + cancel IDOR + webhook still captures

### Sprint K
- [x] Bookings FE real auth
- [x] Home attention / detail honesty
- [x] Admin dead-letters + Failures UI
- [x] Master plan 21–25 honesty

### Sprint L
- [x] TBO gated or real (`INVENTORY_SUPPLIERS`, SIM-TBO labels)
- [x] E2E rewritten to current routes/worker
- [x] E2E green ×2 recorded (`docs/e2e-runs.md` — Sprint P)

### Sprint M–N
- [x] Render blueprint + worker env parity + Sentry hooks (code)
- [x] Ops: pay-failed runbook + refund SOP + Phase 28 checklist
- [x] FIX-P30-01 refresh_quote + bookings org gate
- [ ] Render + Vercel smoke (needs account secrets — `docs/ops/HOSTED_SMOKE.md`)
- [ ] Phase 28 commercial sign-off (Nilesh)
- [x] Sprint N pilot pack (tracker / quickstart / demo / support)
- [ ] Pilot tracker **real** agent data (Nilesh)
- [ ] Phase 29 exit ≥3 paid bookings

---

## Sign-off

| Role | Action |
|---|---|
| Farhan | Execute sprints; hand Nilesh the pilot pack (`agent-quickstart`, tracker, demo script) |
| Nilesh | Sign commercial checklist; fill **real** agent shortlist; schedule demos |
| Sahil | Real supplier sandbox credentials before Phase 25 exit |

**This document is the source of truth for Phases 21–30 until sprints close.** Do not trust master-plan `[x]` for 21–25 without the checklist above.
