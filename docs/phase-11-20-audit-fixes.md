# TripOS — Phase 11→20 Audit & Required Fixes

### Code + docs audit against `tripos-master-plan.md` Phases 11–20

**Audit date:** 2026-09-16  
**Claimed status:** Development complete through Phase 20 (master plan checkboxes largely `[x]`)  
**Audit verdict:** **Not Phase-20 complete.** A usable **prototype loop** exists (mock search → quote → wa.me → mock pay webhook → outbox stub), but several **P0 bugs** break the happy path, and Phases **18–20** are **mock/partial**, not exit-complete. Master plan checkboxes **overstate** readiness.

**Do not claim “live money” or “reliable async fulfillment” until P0/P1 below are fixed.**  
**Phase 21** (real booking confirm engine) is correctly still unchecked in the master plan — but the current worker already pretends to confirm bookings and will crash (`QuoteStatus.booked`).

**Related:** Phase 0 commercial + Razorpay/merchant answers remain open (`phase-0-10-audit-fixes.md` FIX-06) — still blocks honest Phase 18/19 “test mode gateway” exit.

---

## Sprint D status (2026-09-16)

| Fix | Status |
|---|---|
| FIX-P11-01 `QuoteItem.offer_snapshot` relationship | **Done** |
| FIX-P11-02 Real `search_request_id` search → builder | **Done** |
| FIX-P11-06 Deduplicate `/q/[token]` | **Done** (deleted stale `(public)/q`; canonical `app/q/[token]`) |
| FIX-P11-03 Worker `AsyncSessionLocal` import | **Done** |
| FIX-P11-04 `jobs_outbox.attempts` migration | **Done** (`c3d4e5f6a7b8`) |
| FIX-P11-05 `QuoteStatus.booked` crash | **Done** (quote stays `paid`; Booking row confirmed) |

**After pull:** `alembic upgrade head` then run API + `python worker.py` from `apps/api`.

**Sprint D exit:** Search → quote → ready → public view → mock pay webhook → job completes without crash.

---

## Sprint E status (2026-09-16)

| Fix | Status |
|---|---|
| FIX-P11-07 Revalidate before pay + mock failure modes | **Done** (`FARE-CHG` / `SOLD-OUT` fixtures; pay blocked with codes) |
| FIX-P11-09 Payment URL + signature / mock honesty | **Done** (`payment_link_url` col; HMAC when secret set; `payments-v1-mock.md`) |
| FIX-P11-11 Public OG/brand + status page | **Done** |
| FIX-P11-12 Pax gate flight vs hotel | **Done** (search pax count / hotel min 1) |
| FIX-P11-13 Master plan honesty 18–19 | **Done** |

**After pull:** `alembic upgrade head` (includes `d4e5f6a7b8c9` payment_link_url).

---

## Executive scorecard

| Phase | Master plan marks | Audit result | One-line |
|---|---|---|---|
| **11** Adapter + mock | DONE | **MOSTLY DONE** | Contract + FARE-CHG/SOLD-OUT + pytest (Sprint F); Retry-After N/A for mock |
| **12** Inventory search BE | DONE | **MOSTLY DONE** | Search + rate limit; Redis skipped; revalidate-before-book → Phase 21 |
| **13** Search FE | DONE | **DONE** | Real hub/forms/results; `search_request_id` wired |
| **14** Quotes BE | DONE | **MOSTLY DONE** | Org-scoped mutations (Sprint G); extend-expiry still open |
| **15** Quotes FE | DONE | **MOSTLY DONE** | Real `search_request_id` wired |
| **16** wa.me | DONE | **MOSTLY DONE** | MessagingProvider + `wa_me_url` + FRONTEND_URL |
| **17** Public quote | DONE | **MOSTLY DONE** | Agency brand + OG title + status; OG image optional |
| **18** Payments BE | MOCK | **MOCK-COMPLETE** | Mock link + HMAC + amount verify (Sprint G) |
| **19** Payments UI | PARTIAL | **PARTIAL** | Agent UI + status page; live Razorpay E2E still open |
| **20** Outbox/worker | PARTIAL | **MOSTLY DONE** | SKIP LOCKED + stale reclaim (Sprint G); booking confirm still stub |

\*“MOSTLY DONE” = usable for demos with caveats; not exit-criteria complete.

---

## Priority legend

| Priority | Meaning |
|---|---|
| **P0** | Fix before trusting the commercial loop — broken or will crash |
| **P1** | Required to honestly close Phases 11–20 |
| **P2** | Important plan alignment before Phase 21+ / live suppliers |
| **P3** | Enhancement / polish |

---

# P0 — Critical blockers (fix first)

---

### FIX-P11-01 — `QuoteItem.offer_snapshot` relationship missing (breaks public + ready)

**Phases:** 14, 17  
**Files:** `apps/api/app/models/commercial.py`, `apps/api/app/api/public.py`, `apps/api/app/services/quotes.py`

**Problem:**
- `QuoteItem` has `offer_snapshot_id` FK but **no** `offer_snapshot` relationship.
- Code does `selectinload(QuoteItem.offer_snapshot)` in public quote + `mark_quote_ready` (`# type: ignore`).
- Public quote sanitization / ready path will fail at runtime (AttributeError / InvalidRequestError).

**Required fix:**
- [x] Add both sides of the relationship (`QuoteItem.offer_snapshot` ↔ `OfferSnapshot` reverse if needed)
- [x] Remove `# type: ignore` once typed cleanly
- [ ] API test: create quote → ready → `GET /public/quotes/{token}` returns sanitized titles

**Acceptance:** Public quote and mark-ready succeed against migrated DB.

---

### FIX-P11-02 — Quote builder sends invalid `search_request_id` (FK failure)

**Phases:** 13–15  
**Files:** `apps/web/src/app/(agent)/app/quotes/new/page.tsx`, `apps/web/src/lib/quoteSlice.ts`, inventory search response

**Problem:**
- Builder hardcodes `search_request_id: "00000000-0000-0000-0000-000000000000"`.
- Backend `OfferSnapshot.search_request_id` FKs to `search_requests.id`.
- Creating a quote from the UI will fail unless that UUID exists (it does not).

**Required fix:**
- [x] Persist `search_request_id` from `SearchResponse` into Redux (or pass with each offer)
- [x] Builder sends the real UUID per item
- [ ] Manual/API test: search → add offer → create quote → 201

**Acceptance:** UI quote create works end-to-end with mock search.

---

### FIX-P11-03 — Worker cannot start (`async_session_maker` import)

**Phase:** 20  
**Files:** `apps/api/worker.py`, `apps/api/app/db/session.py`

**Problem:**
- Worker imports `from app.db.session import async_session_maker`
- Session module exports **`AsyncSessionLocal`** only → **ImportError** on worker boot.

**Required fix:**
- [x] Align import/export names
- [x] Document how to run worker locally (`python worker.py` from `apps/api`)

**Acceptance:** Worker process starts and polls without import crash.

---

### FIX-P11-04 — `jobs_outbox.attempts` used in code but missing from migration

**Phase:** 20  
**Files:** `apps/api/app/models/commercial.py`, `apps/api/worker.py`, Alembic initial schema

**Problem:**
- Model + worker use `job.attempts` for retries.
- Initial migration `jobs_outbox` has **no `attempts` column**.
- Worker retries will raise DB errors on commit.

**Required fix:**
- [x] Alembic migration: add `attempts INTEGER NOT NULL DEFAULT 0`
- [x] Align model default with DB

**Acceptance:** Failed job increments attempts and schedules backoff without SQL errors.

---

### FIX-P11-05 — Booking confirm sets invalid `QuoteStatus.booked`

**Phases:** 20 (handler pretends Phase 21)  
**Files:** `apps/api/app/services/jobs.py`, `apps/api/app/models/enums.py`

**Problem:**
- `handle_booking_confirm` does `quote.status = QuoteStatus.booked`
- Enum is only: `draft | ready | sent | paid | expired | cancelled`
- **AttributeError** (or invalid enum write) when outbox job runs after pay webhook.

**Required fix (choose one for V1 honesty):**
- [x] **A (recommended until Phase 21):** Keep quote at `paid`; only create/update `Booking` row; do not invent quote status
- [ ] **B:** Add `booked` to enum + migration + update status machine docs
- [x] Do not call adapter until Phase 21 — but stop crashing the job

**Acceptance:** After simulated webhook, outbox job completes without enum crash; quote/booking states are coherent.

---

### FIX-P11-06 — Duplicate `/q/[token]` routes (stale placeholder vs real page)

**Phase:** 17  
**Files:** `apps/web/src/app/q/[token]/*`, `apps/web/src/app/(public)/q/[token]/page.tsx`

**Problem:**
- Real public quote lives under `app/q/[token]`.
- Stale Sprint-B placeholder still at `(public)/q/[token]` (“Phase 14+”).
- Next.js route conflict / ambiguous which page wins.

**Required fix:**
- [x] Delete or redirect `(public)/q/[token]` to the real implementation
- [x] Keep one public layout shell for quote pages *(legacy `(public)/quote/[id]` redirect remains)*
- [ ] Verify `/q/{token}` renders itinerary (not placeholder)

**Acceptance:** Single public quote page; no leftover “Phase 14+” copy.

---

# P1 — Required to close Phases 11–20 honestly

---

### FIX-P11-07 — Revalidate never simulates failure; not called before ready/pay/book

**Phases:** 11, 12, 14, 18  
**Files:** `mock_adapter.py`, `services/quotes.py`, `services/payments.py`, `services/jobs.py`

**Gaps:**
- Mock `revalidate` always succeeds (no fare_changed / sold_out).
- Quote ready / create payment / booking job **do not** call revalidate.
- Plan requires revalidate before pay link and before book; distinct error codes.

**Required:**
- [x] Mock flag or deterministic path to simulate fare change / sold out
- [x] Call revalidate before mark-ready (optional) and **required** before create payment link
- [x] Map failures to clear API errors (`fare_changed`, `sold_out`, `timeout`)
- [ ] Booking job (Phase 21) must use same taxonomy — do not leave fake confirm as “done”

**Acceptance:** Agent sees clear error when mock fare changes; pay link blocked.

---

### FIX-P11-08 — Adapter interface incomplete vs plan (`status`, `map_error`)

**Phase:** 11  
**Files:** `apps/api/app/adapters/base.py`, mock + registry

**Required:**
- [x] Add `status` and `map_error` to `BaseAdapter` (or document deliberate deferral in ADR)
- [x] Mock implements stubs
- [x] Prefer real **pytest contract tests** under `apps/api/tests/` (scripts alone ≠ Phase 11 exit)

**Acceptance:** Interface matches master plan or written exception; contract test runs in CI-ready form.

---

### FIX-P11-09 — Payments are mock-only; webhook signature disabled

**Phases:** 18–19  
**Files:** `services/payments.py`, `api/webhooks.py`, config env

**Gaps:**
- `_mock_create_razorpay_link` only; Razorpay keys unused.
- Signature verify commented out.
- Create path discards payment URL (`order_id, _ = ...`); public builds a **different** mock URL from `gateway_order_id`.
- No column to store `payment_link_url`.
- Idempotency helper stub always `True` and unused.
- Phase 19 exit (“test payment in Razorpay test mode”) **not met**.

**Required for honest Phase 18/19:**
- [x] Persist payment link URL on `Payment` (migration)
- [x] Use same URL for agent + public CTA
- [x] Implement webhook HMAC verify when secret present; reject invalid signatures
- [x] Wire Razorpay test SDK **or** formally mark Phase 18/19 as **MOCK-COMPLETE** and reopen checkboxes
- [x] Replace/implement `check_idempotency_key` before relying on it
- [ ] Do not mark Phase 19 DONE until one real Razorpay test capture updates DB (needs Phase 0 merchant + keys)

**Acceptance:** Either documented mock mode with honest master-plan status, or live test-mode capture works.

---

### FIX-P11-10 — Worker locking / deploy path incomplete

**Phase:** 20  
**Files:** `apps/api/worker.py`, `apps/worker/`, Render docs

**Gaps:**
- `FOR UPDATE SKIP LOCKED` commented out (Postgres is the real DB — should enable).
- `apps/worker/` is empty `.gitkeep`; real entry is `apps/api/worker.py` (OK if documented).
- No Render worker service runbook in-repo.
- Expire-quotes runs every poll iteration (OK for prototype; document or throttle).

**Required:**
- [x] Enable `with_for_update(skip_locked=True)` for Postgres
- [x] README: how to run API + worker locally and on Render
- [x] Align `apps/worker` stub README pointing at `apps/api/worker.py`

**Acceptance:** Two worker processes do not double-process the same job.

---

### FIX-P11-11 — Public quote OG / agency brand / status return page incomplete

**Phase:** 17 (+19 public return)  
**Files:** `app/q/[token]/page.tsx`, `PublicQuoteClient.tsx`, `status/page.tsx`

**Gaps:**
- OG title not `"Travel Quote from {agency_name}"`; hardcoded TripOS.
- No OG image asset.
- Agency `brand_name` / logo not shown (header says TripOS).
- `/q/[token]/status` still “Preparing Payment Gateway / Phase 18”.
- Metadata fetch URL mixes `NEXT_PUBLIC_API_URL` with/without `/api/v1` inconsistently.

**Required:**
- [x] Include org brand on public page + OG title/description
- [x] Fix absolute API base for metadata fetch
- [x] Status page: post-pay messaging (pending / success / failed) — not Phase-18 placeholder
- [ ] Optional static OG image

**Acceptance:** Logged-out customer sees agency-forward quote; status page matches payment state.

---

### FIX-P11-12 — Pax gate too weak vs plan (flight full pax / hotel guest min)

**Phase:** 14  
**Files:** `services/quotes.py` `mark_quote_ready`

**Problem:** Any non-empty passenger list with names is enough; no flight vs hotel rules; no count vs search intent.

**Required:**
- [x] Flights: require full pax set (count/type as available from offer/search)
- [x] Hotels: guest minimum rule documented + enforced
- [x] Block create-pay-link if pax incomplete (also enforce in payments service, not only ready)

**Acceptance:** Incomplete pax cannot reach payment link.

---

### FIX-P11-13 — Master plan honesty patch (Phases 11–20)

**Files:** `docs/tripos-master-plan.md`

**Required:**
- [x] Re-open or annotate checkboxes that are mock/partial (especially 18.3, 19.3–19.4, 20.2 SKIP LOCKED, 11.2 fare-change, 14 revalidate-before-pay)
- [x] Add note under Phase 20: “Prototype worker; see `docs/phase-11-20-audit-fixes.md`”
- [x] Do not treat current `[x]` as exit-complete for pilot money

---

# P2 — Plan alignment & quality (before Phase 21 / live suppliers)

---

### FIX-P11-14 — Inventory supplier selection hardcoded

**Files:** `services/inventory.py`

- [x] Resolve active suppliers from DB (`Supplier` / `SupplierConfig`) or document “mock-only until Phase 25”
- [x] Stop hardcoding `["mock_supplier"]` without comment + ADR

---

### FIX-P11-15 — No Redis/Upstash search cache

**Phase:** 12.1

- [x] Implement short-TTL cache **or** amend plan: “optional; skipped for V1 pilot”
- [x] If skipped, uncheck master plan item and document

---

### FIX-P11-16 — Quote expiry extend ≤24h + % markup

**Phase:** 14–15

- [ ] API + UI to extend `valid_until` with fare-risk warning (cap 24h from create)
- [ ] Support % markup or document “flat ₹ (paise) only in V1”

---

### FIX-P11-17 — Messaging provider port missing

**Phase:** 16

- [x] Add swappable MessagingProvider interface (wa.me impl now; Cloud API later)
- [x] Optionally return `wa_me_url` from backend (frontend currently builds it)

---

### FIX-P11-18 — Encryption stub still dangerous

**Carry-over from Phase 0–10 FIX-19**  
**Files:** `utils/encryption.py`

- [x] Do not store real supplier secrets until Fernet/KMS is real
- [x] Guard write paths so stub encrypt cannot be used in `ENV=production`

---

### FIX-P11-19 — Payment / quote financial edge cases

- [ ] Razorpay link expiry aligned to `valid_until` when using real gateway
- [ ] `payment_captured_quote_expired` → durable ops signal (not log-only job)
- [ ] Refund initiate remains manual stub — document clearly
- [ ] Fix `create_payment_for_quote` unused/broken `select.undefer_group` refresh path (use `selectinload` items)

---

### FIX-P11-20 — Dashboard still fake metrics

**File:** `apps/web/src/app/(agent)/app/page.tsx`

- [x] Wire real counts (customers/quotes/payments) or label as placeholder
- [x] Avoid implying live GMV

---

### FIX-P11-21 — Tests are scripts, not pytest

**Files:** `apps/api/scripts/test_*.py`

- [x] Prefer `apps/api/tests/` with pytest for adapters, quotes public sanitize, webhook idempotency
- [x] Keep scripts as optional smoke only

---

### FIX-P11-22 — Root `adapters/` package unused

- [x] Point README at `apps/api/app/adapters/` **or** re-export from root package
- [x] Avoid two “homes” for adapters

---

# P3 — Enhancements (optional now)

---

### ENH-P11-01 — Customer timeline still empty

- [ ] Append quote.sent / payment.captured events when those modules fire (bridges Phase 10 + 23)

### ENH-P11-02 — Agent quote detail snapshot display

- [ ] Show offer title/description from snapshot, not raw snapshot id

### ENH-P11-03 — Load-more / sort polish on search

- [ ] Confirm default sort price ascending end-to-end; expose sort toggle if needed

### ENH-P11-04 — Audit events for commercial loop

- [ ] Write `audit_events` on quote.sent, payment.captured (prepares Phase 23)

### ENH-P11-05 — Bookings UI ComingSoon

- [ ] Correct — belongs to Phase 22; do not mark done early

---

# Risks (if ignored)

| Risk | Impact |
|---|---|
| Fake `search_request_id` | Quote create from UI always fails |
| Missing `offer_snapshot` relation | Public quote / ready broken |
| Worker import + `attempts` column | Async backbone does not run |
| `QuoteStatus.booked` | Post-pay job dies; money captured with no coherent state |
| Mock Razorpay marked DONE | False confidence before pilot money |
| Webhook without signature | Anyone can mark quotes paid |
| Stub encryption used for supplier creds | Credential leakage |
| Duplicate `/q` routes | Wrong page shipped / confused customers |
| Master plan all `[x]` | Technical debt compounds into Phase 21–25 |

---

# What is actually in good shape

- Mock adapter deterministic flight/hotel search + fake PNR book/cancel
- Inventory HTTP API + in-memory org rate limit (30/min) + offer cap 50
- Search UI (forms, results, add-to-quote Redux, one product type rule)
- Quote model + public token (`secrets.token_urlsafe`) + 4h/12h default expiry
- Quotes list/builder/detail/send pages (scaffold quality)
- wa.me preview + E.164 validation + messages log + mark `sent`
- Public quote client with expiry banner + sticky pay affordance (when URL present)
- Payment row + outbox enqueue on mock webhook; expired-quote manual review job type
- Worker poll loop design (needs bugfixes above)
- Manual smoke scripts for adapters / inventory / quotes / webhook

---

# Suggested fix order (execution sprints)

### Sprint D — Unblock the mock commercial loop (1–2 days) — **DONE 2026-09-16**
1. FIX-P11-01 Offer snapshot relationship  
2. FIX-P11-02 Real `search_request_id` from search → builder  
3. FIX-P11-06 Deduplicate `/q/[token]`  
4. FIX-P11-03 Worker session import  
5. FIX-P11-04 `attempts` migration  
6. FIX-P11-05 Fix `QuoteStatus.booked` crash  

**Exit:** Search → quote → ready → public view → mock pay webhook → job completes without crash.

### Sprint E — Honesty for pay + revalidate (2–3 days) — **DONE 2026-09-16**
7. FIX-P11-07 Revalidate before pay + mock failure modes  
8. FIX-P11-09 Payment URL persistence + signature verify (or formal MOCK status)  
9. FIX-P11-11 Public OG/brand + status page  
10. FIX-P11-12 Pax gate rules  
11. FIX-P11-13 Master plan checkbox honesty  

### Sprint F — Worker + platform polish (1–2 days) — **DONE 2026-09-16**
12. FIX-P11-10 SKIP LOCKED + runbooks  
13. FIX-P11-08 Adapter status/map_error + pytest contracts  
14. FIX-P11-14–22 as needed before Phase 21 (16/19 left open as non-blocking polish)

**Then:** Re-audit Phases 11–20 → only then start **Phase 21** real booking confirm (revalidate → adapter.book → failure_reason taxonomy).

---

## Sign-off

| Role | Action |
|---|---|
| Farhan | Execute Sprint D immediately (P0 loop blockers) |
| Nilesh | Still required for Phase 0 commercial / Razorpay merchant (blocks honest Phase 19) |
| Sahil | Supplier sandbox when Phase 25; mock continues until then |

**Companion docs:** `docs/phase-0-10-audit-fixes.md` · `docs/architecture/phase-4-schema-decisions.md` · `docs/architecture/v1-api-layout.md`
