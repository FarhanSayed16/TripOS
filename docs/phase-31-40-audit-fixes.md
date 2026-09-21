# TripOS — Phase 31→40 Audit & Required Fixes

### Code + docs audit against `tripos-master-plan.md` Phases 31–40

**Audit date:** 2026-09-19  
**Claimed status:** Development complete through Phase 40  
**Audit verdict:** **Not Phase-40 complete.** Substantial **V2/V3 scaffolding** exists (packages, wallet, follow-ups, AI, white-label domains, supplier strategy UI), but **exit criteria are unmet**, several features are **prototype-quality or insecure**, and **Phase 31 GO/NO-GO was skipped** while later phases were built.

**Do not claim “complete through Phase 40.”**  
**Do not treat presence of routes/pages as phase completion.**  
**Prior audits (0–30 / Sprints J–N) still apply** — pilot/hosted/commercial gates remain open.

**Related docs:** `phases-31-40-implementation-tasks.md` (task list; preamble overstates “Phases 1–30 complete”), `v1-exit-decision.md` (unfilled stub), `tripos-ai-spec.md`.

---

## Executive scorecard

| Phase | Master plan | Audit result | One-line |
|---|---|---|---|
| **31** V1 exit gate | all `[ ]` | **NOT DONE** | Metrics UI exists; **no written GO/NO-GO** |
| **32** Packages | all `[ ]` | **PARTIAL** | CRUD → draft quote; no versioning / live inventory |
| **33** Commission & wallet | all `[ ]` | **PARTIAL** | Ledger stack exists; reconciliation unproven |
| **34** Follow-ups & docs | all `[ ]` | **PARTIAL / RISK** | Follow-ups OK; vault = local disk + **unauth download** |
| **35** AI Copilot | all `[ ]` | **PARTIAL** | Monolith OpenAI prototype; not `apps/ai` service |
| **36** Multi-supplier | all `[ ]` | **PARTIAL / WEAK** | CB + UI; failover not real; TBO still simulated |
| **37** White-label | all `[ ]` | **PARTIAL** | Domains + theme hooks; no verified custom domain |
| **38** Distributor hierarchy | all `[ ]` | **PARTIAL / WEAK** | Sub-agent create; hardcoded 20%; weak RBAC |
| **39** Scale / ops | all `[ ]` | **PARTIAL** | Logs/Sentry/runbooks; metrics/on-call incomplete |
| **40** Backlog cadence | all `[ ]` | **NOT DONE** | Templates only; process not running |

**Overall:** Early **V2/V3 spike ahead of Phase 31 discipline**. Treat 32–38 as **prototype**, not shipped product.

---

## Honesty / process violations (fix first)

### FIX-P31-00 — Claimed Phase 40 complete is false

**Severity:** CRITICAL · **Category:** honesty  

**Problem:** User claim “complete through Phase 40” contradicts master-plan checkboxes (all still `[ ]`) and unmet exits.

**Required:**
- [ ] Stop using “complete through Phase 40”
- [ ] Treat this document as source of truth for 31–40 until sprints close
- [ ] Correct `phases-31-40-implementation-tasks.md` preamble (“Phases 1–30 are complete”) — still inaccurate per prior audits

---

### FIX-P31-01 — Phase 31 GO/NO-GO never recorded (built V2/V3 anyway)

**Severity:** CRITICAL · **Category:** process / scope  

**Files:** `docs/v1-exit-decision.md`, master plan §31  

**Problem:** Decision stub is all TBD. Packages, wallet, AI, white-label, hierarchy already in the tree — violates “V2 unlocked only on GO.”

**Required:**
- [ ] Fill metrics from `/admin/analytics` (or waive with founder signature)
- [ ] Record explicit **GO V2** or **FIX V1 longer** in `v1-exit-decision.md`
- [ ] If FIX V1: freeze feature work on 32–38 until V1 exits (pilot + hosted smoke) close
- [ ] If GO V2: annotate which phases are **prototype** vs **exit-complete**

**Acceptance:** One signed decision file exists before more V2/V3 build.

---

# P0 — Ship blockers / security

---

### FIX-P34-01 — Document download is unauthenticated (IDOR / data leak)

**Phase:** 34  
**Severity:** CRITICAL · **Category:** security  
**Files:** `apps/api/app/api/documents.py` `download_document`

**Problem:**  
`GET /documents/{filename}/download` has auth **commented out**. Anyone who guesses/leaks a filename can download tickets/vouchers. Storage is local `uploads/` (not S3/R2).

**Required:**
- [ ] Require `require_active_org` (or short-lived signed URL)
- [ ] Authorize via `BookingDocument.organization_id` + filename ownership
- [ ] Block path traversal (`..`, absolute paths)
- [ ] Move to S3/R2 (or clearly label “dev-only local storage” and disable in production)

**Acceptance:** Unauthenticated download → 401/403; cross-org → 404.

---

### FIX-P35-01 — AI enabled by default + unsafe search fallbacks

**Phase:** 35  
**Severity:** HIGH · **Category:** safety / cost  
**Files:** `app/core/config.py` (`AI_COPILOT_ENABLED: bool = True`), `app/services/ai_copilot.py` / `api/ai.py`

**Problem:**  
Copilot defaults **on**. Incomplete parse can fall back to hard-coded destination/date (e.g. DEL / fixed date) — agents may search wrong inventory silently.

**Required:**
- [ ] Default `AI_COPILOT_ENABLED=False` in production (opt-in)
- [ ] Reject incomplete intents instead of inventing origin/destination/date
- [ ] Keep “never invent prices / offer IDs” tests green
- [ ] Require `OPENAI_API_KEY` clearly documented; fail closed

**Acceptance:** Missing fields → clear error; no silent default city/date in prod.

---

### FIX-P36-01 — “Failover” strategy does not fail over

**Phase:** 36  
**Severity:** HIGH · **Category:** bug / honesty  
**Files:** `services/inventory.py`, `services/supplier_strategy.py`, admin suppliers UI

**Problem:**  
All strategies currently fan out with `asyncio.gather` (parallel). Killing primary does not prove sequential failover. TBO remains **simulated**. Exit “kill primary → still get offers” is not met.

**Required:**
- [ ] Implement real `failover` / `primary_only` behavior (sequential; stop on first success for failover)
- [ ] Align UI copy with actual behavior
- [ ] Keep `INVENTORY_SUPPLIERS` gate; do not present simulated TBO as live
- [ ] Add staging test for kill-switch / circuit-open primary

**Acceptance:** Documented strategy modes match runtime; staging failover test recorded.

---

### FIX-P38-01 — Hierarchy RBAC / commission waterfall incomplete

**Phase:** 38  
**Severity:** HIGH · **Category:** security / money  
**Files:** `services/commissions.py`, `organizations` network APIs, `app/network` UI

**Problem:**  
Master/sub-agent create exists, but commission waterfall is **hardcoded 20%/80%**. Network GMV shows placeholders. No proven sibling isolation / limited nav for sub-agents beyond basic org scope.

**Required:**
- [ ] Configurable waterfall rules (Phase 0 commercial)
- [ ] Automated test: sub-agent cannot read sibling org quotes/customers
- [ ] Master network aggregates real (or remove “Coming Soon” GMV lie)
- [ ] Sub-agent nav/data scoping if product requires limited roles

**Acceptance:** Sibling isolation test green; commission split visible and configurable.

---

# P1 — Required to honestly close each phase

---

### FIX-P32-01 — Packages: versioning + real inventory backing

**Phase:** 32  
**Files:** `models/packages.py`, `api/packages.py`, admin/agent package UIs  

**Gaps:** No package versioning; `to-quote` uses estimated costs / default markup; not proven through pay→book.

**Required:**
- [ ] Versioning model **or** document “V1 packages = snapshot only”
- [ ] Prefer linking package items to revalidated offers / search snapshots
- [ ] One end-to-end: publish → agent quote → pay → booking (mock OK)
- [ ] Uncheck plan exit until that run is recorded

---

### FIX-P33-01 — Wallet ledger reconciliation proof

**Phase:** 33  
**Files:** `models/wallet.py`, `services/commissions.py`, admin commissions / agent wallet  

**Required:**
- [ ] Document formula vs Phase 0 commercial answers
- [ ] Reconcile N sample bookings (spreadsheet or pytest) pending/available/paid
- [ ] Clear UI distinction: platform_fee vs agent_markup vs commission
- [ ] Statement export verified against ledger

---

### FIX-P34-02 — Document vault = object storage + re-share

**Phase:** 34  

**Required:**
- [ ] S3 or Cloudflare R2 integration (presigned upload/download)
- [ ] Org-scoped auth on all document routes
- [ ] wa.me helper to re-share ticket/voucher link
- [ ] Retention / max size / mime allowlist

---

### FIX-P34-03 — Follow-ups exit proof

**Phase:** 34  
**Files:** `worker.check_unpaid_followups`, `api/followups.py`, agent follow-ups UI  

**Required:**
- [ ] Record one unpaid quote → 24h/48h nudge created
- [ ] Snooze/dismiss audited
- [ ] Optional reminder wa.me works on mobile

---

### FIX-P35-02 — AI architecture vs master plan / spec

**Phase:** 35  
**Files:** `apps/ai/.gitkeep`, `api/ai.py`, `tripos-ai-spec.md`  

**Gaps:** Spec calls for separate `apps/ai` with `/ai/v1/parse-intent` + `format-quote-draft`. Implementation is inlined in main API with different paths.

**Required (pick one and document):**
- [ ] **A:** Extract `apps/ai` service + gateway auth as planned, **or**
- [ ] **B:** Amend master plan / `tripos-ai-spec.md` to accept monolith AI for V2
- [ ] Eval set of real agent phrases
- [ ] Pilot proof: ≥1 successful draft→quote on real search results
- [ ] Deploy story + key ownership

---

### FIX-P36-02 — Second live supplier + booking supplier_code

**Phase:** 36  

**Required:**
- [ ] Real httpx adapter (TBO or TripJack) with encrypted credentials
- [ ] Persist `supplier_code` (and refs) on booking row or equivalent
- [ ] Admin kill switch proven in staging
- [ ] Defer `merge_dedupe` until failover stable (plan already says optional)

---

### FIX-P37-01 — White-label exit: verified custom domain

**Phase:** 37  
**Files:** `OrganizationDomain`, `GET /public/theme/{domain}`, `PublicQuoteClient`, `admin/branding`  

**Gaps:** Branding page not in admin nav; domain verification stub; no lead form → CRM.

**Required:**
- [ ] Add Branding to admin nav
- [ ] Domain verification flow (DNS TXT or Vercel domain link)
- [ ] One agency custom domain serves branded quote + pay status
- [ ] Minimize TripOS chrome for WL tenants
- [ ] Optional: public lead form → CRM (or uncheck)

---

### FIX-P39-01 — Ops maturity gaps

**Phase:** 39  

**Required:**
- [ ] Metrics beyond logs: book success rate, webhook failures, dead-letter spike (dashboard or Sentry alerts)
- [ ] Search cache decision (still skipped) documented or implemented
- [ ] Worker concurrency / multi-instance notes
- [ ] Postgres backup **restore dry-run** executed once (not only documented)
- [ ] On-call checklist dedicated to Phase 39 (link ops runbooks)

---

### FIX-P40-01 — Start the perpetual process

**Phase:** 40  
**Files:** `docs/quarterly-review-template.md`, `docs/backlog.md`  

**Required:**
- [ ] First monthly metrics review dated
- [ ] Triage `backlog.md` + `tripos-enhancements.md` into V1.5 / V2 / V3 / Park
- [ ] Update master-plan checkboxes when work is accepted or rejected
- [ ] Keep `tripos-docs-index.md` accurate

---

# P2 — Carry-over from 0–30 / ENHs (still open)

These block honest “V1 complete” and should not be forgotten while chasing V2/V3:

| ID | Item | Status |
|---|---|---|
| Hosted smoke | Render + Vercel + secrets | Open (Sprint M) |
| E2E green ×2 | Postgres required | Open (Sprint L) |
| Commercial sign-off | Nilesh checklist | Open (Sprint I/N) |
| Pilot ≥3 paid | Real agents | Open (Sprint N) |
| Real TBO | Simulated only | Open (P25) |
| ENH-02 | WhatsApp message presets | Missing |
| ENH-03 | Phone merge UX | Missing |
| ENH-05 | Compensate cancel on multi-item partial book | Missing |
| ENH-06 | Next.js `middleware.ts` for `/app` `/admin` | Missing |
| Settings page | Still `ComingSoon` | Missing |
| Admin branding nav | Page exists, not linked | Gap (P37) |

ENH-01 (timeline bookings) appears **done**.

---

# P3 — Enhancements / risks (optional)

| ID | Item | Notes |
|---|---|---|
| ENH-31 | Agent-facing analytics | Admin-only GMV today |
| ENH-32 | Package versioning UI | Diff / rollback |
| ENH-33 | Auto-settle commissions | Dangerous without commercial lock |
| ENH-34 | WhatsApp Cloud API | Still wa.me by design; not in 31–40 plan |
| ENH-35 | PWA / native mobile | Responsive only |
| ENH-36 | Hotel full lifecycle | Mock hotel search exists; no hotel supplier lifecycle |
| RISK-01 | V2/V3 code without Phase 31 GO | Scope debt |
| RISK-02 | AI cost/abuse if flag default true | See FIX-P35-01 |
| RISK-03 | Local `uploads/` on ephemeral Render disk | Data loss |

---

## What is solid (do not regress)

- Core V1 loop scaffolding from Sprints J–N (audit, cancel org-scope, confirm backoff, failures UI, mock inventory gate)
- Admin analytics endpoint + page (useful for Phase 31 metrics)
- Follow-up detector + agent inbox pattern
- Circuit breaker hooks + supplier admin UI (even if failover incomplete)
- Structlog + Sentry wiring + ops runbooks under `docs/ops/`
- Org scoping patterns (`require_active_org`) on most new routers — **except document download**

---

## Suggested fix sprints (31–40)

### Sprint O — Honesty + security (1–2 days) — **DONE 2026-09-19**
1. FIX-P31-00 / P31-01 — Exit decision stub + stop “Phase 40 done” claim ✅  
2. FIX-P34-01 — Auth document download (+ path traversal) ✅  
3. FIX-P35-01 — AI default off + no silent search fallbacks ✅  
4. Uncheck / annotate overstated task-doc preamble ✅  

**Exit:** Safe to continue building; no open file IDOR; AI fail-closed. (Phase 31 GO/FIX still unsigned — Sprint P.)

### Sprint P — Close V1 before more V2 — **ENGINEERING DONE 2026-09-19** (product gates open)
5. Hosted smoke + E2E greens + Nilesh commercial + pilot tracker (Sprint I/L/M/N leftovers)  
6. Phase 31 decision → **FIX V1 LONGER** until hosted/commercial/pilot close  

**Exit (honest):** E2E green ×2 recorded. Hosted smoke + commercial + pilot still Nilesh/accounts-blocked — see `docs/sprint-p-status.md`.

### Sprint Q — Package + wallet + follow-ups — **ENGINEERING DONE 2026-09-19**
7. FIX-P32-01, FIX-P33-01, FIX-P34-02/03  

**Exit:** Snapshot packages honesty + wallet formula/tests; vault mime/size/share-link (R2 client deferred); follow-up audits. See `docs/sprint-qrst-status.md`.

### Sprint R — AI + multi-supplier honesty — **ENGINEERING DONE 2026-09-19**
8. FIX-P35-02, FIX-P36-01/02  

**Exit:** AI Option B documented; sequential failover; booking.supplier_code. Live TBO still simulated.

### Sprint S — White-label + hierarchy — **ENGINEERING DONE 2026-09-19**
9. FIX-P37-01, FIX-P38-01  

**Exit:** Branding nav; domain verify endpoint; configurable override BPS; real network GMV; sibling org-scope tests. Real custom DNS still external.

### Sprint T — Ops + cadence — **ENGINEERING DONE 2026-09-19**
10. FIX-P39-01, FIX-P40-01  

**Exit:** Local restore dry-run recorded; Phase 39 checklist; monthly review + backlog triage.

---

## Checklist (copy to board)

### Sprint O — **DONE 2026-09-19**
- [x] Phase 31 decision stub + honesty (`docs/v1-exit-decision.md` — unsigned; GO/FIX still TBD)
- [x] Document download authenticated + org-scoped + path traversal guards (`documents.py`)
- [x] `AI_COPILOT_ENABLED` default false; no silent DEL/date fallback (`config` / `ai.py` / `.env.example`)
- [x] Task-doc / claim honesty patched (`phases-31-40-implementation-tasks.md` preamble)
- [x] Pytest: `tests/test_sprint_o.py` + updated `tests/test_ai_copilot.py`

### Sprint P (V1 leftovers) — **PARTIAL 2026-09-19**
- [x] E2E green ×2 (`docs/e2e-runs.md` — 15 passed ×2)
- [x] Phase 31 decision recorded as **FIX V1** (`docs/v1-exit-decision.md`)
- [x] Hosted smoke runner + blocker honesty (`scripts/hosted_smoke.py`, `ops/HOSTED_SMOKE.md`)
- [x] Sprint P board (`docs/sprint-p-status.md`) + `tests/test_sprint_p.py`
- [ ] Hosted smoke **executed** against live Render/Vercel (needs accounts)
- [ ] Commercial sign-off (Nilesh)
- [ ] Pilot shortlist / demos (Nilesh)

### Sprint Q–T — **ENGINEERING DONE 2026-09-19** (live exits still external-blocked)
- [x] Packages snapshot honesty + synthetic OfferSnapshot on to-quote
- [x] Wallet formula doc + BPS override + reconcile tests
- [x] Document mime/size + share-link (R2 upload client deferred / 501)
- [x] Follow-up snooze/dismiss/reminder audited
- [x] AI spec Option B (monolith)
- [x] Sequential failover + booking.supplier_code migration
- [x] Branding admin nav + domain verify + network GMV + master BPS
- [x] Local Postgres restore dry-run + Phase 39 checklist
- [x] Monthly review 2026-09 + backlog triage
- [x] Pytest `tests/test_sprint_qrst.py`
- [ ] Hosted R2/S3 upload; live custom domain DNS; live TBO; package pay→book E2E

---

## Sign-off

| Role | Action |
|---|---|
| Farhan | Sprint P engineering closed (E2E); finish hosted smoke when Render/Vercel exist |
| Nilesh | Commercial + pilot shortlist (still blocking honest GO V2 / Phase 31 flip) |
| Sahil | Live supplier credentials before Phase 36 exit |

**This document is the source of truth for Phases 31–40 until sprints close.** Do not trust “complete through Phase 40” or implementation-task checkboxes without the list above.
