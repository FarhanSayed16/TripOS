# TripOS — Flight Commerce Implementation Plan  
### Phase-wise build (FC Phases 0–8)

**Status:** FC Phases 0–8 engineering scaffolds **SHIPPED** (2026-09-28); Phase 0 commercial + Phase 1 live smoke still open externally. Soft-fail cancel, partner hardening, TBO segments mapped (2026-09-29).
**Owners:** Farhan (build) · Sahil (supplier contract / sandbox) · Nilesh (commercial / first live feed)  
**Product shape:** **B2B Agent OS** that aggregates supplier APIs and can later expose APIs to a **separate B2C brand** (no B2C storefront in these phases).

**Companion docs:**  
- Gap analysis (why / for sir) → [`flight-api-features-gap-plan.md`](./flight-api-features-gap-plan.md)  
- L2B readiness (DONE 0–7) → [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md)  
- L2B explained → [`live-inventory-phases-0-7-explained.md`](./live-inventory-phases-0-7-explained.md)

**Rule:** Work **one phase at a time**. Each phase lists **surfaces**, **checklists**, **acceptance**, and **feature IDs** from the Top 25 + currency/i18n so nothing is missed. Do not start Phase N+1 until Phase N exit is checked (or explicitly waived in writing).

---

## 0. How to use this plan

| Term | Meaning |
|---|---|
| **Surface** | Where the work shows up (API / Agent UI / Admin / Worker / Ops / Data) |
| **Feature ID** | Number from gap plan (§1.1 Top 25, §1.2 your adds, §1.3 extras) |
| **Exit** | Definition of “phase done” — must be checkable |

**Prerequisite (already done):** L2B Phases 0–7 engineering closed.  
**Still required before heavy live prod search:** Sahil contract truth + staging smoke (covered in FC Phase 0–1).

```text
Suppliers → TripOS B2B (these phases) → later B2C brand via Partner API (Phase 8)
```

---

## 1. Phase map (8 phases + optional partner)

| Phase | Name | Est. | Closes feature IDs (primary) |
|---|---|---|---|
| **0** | Commercial + capability lock | 0.5–1 wk | Gates 1–6, 8–15, 26–27 feasibility |
| **1** | Live supplier spine | 1–2 wk | 1, 2, 3, 6, 18, 24, 29, 32, 35 |
| **2** | Fare rules + cancel/refund + ops visibility | 1–2 wk | 14, 15, 20, 21 (partial), 36, 39 |
| **3** | Aggregation + ranking + hotel parity | 1–2 wk | 16, 17, 33 |
| **4** | Global currency | 1–2 wk | **26** |
| **5** | Multilingual (i18n) | 1–2 wk | **27** |
| **6** | Fare families + ancillaries + seats | 2–4 wk | 8, 9, 10, 37 (partial) |
| **7** | Servicing + richer content | 2–4 wk | 4, 5, 7, 11, 12, 13, 22, 23, 30, 31, 38 |
| **8** | Partner / B2C-facing API | 2–3 wk | 25, 40 (+ B2C bridge) |

**Recommended order:** 0 → 1 → 2 → 3, then **4 ∥ 5** (parallel OK), then 6 → 7 → 8.

**Two-stream option after Phase 3:**  
- Stream A: Phase 6 → 7 (content/servicing)  
- Stream B: Phase 4 → 5 (currency/i18n) — can start as soon as Phase 1 exit is green

---

## 2. Coverage matrix (nothing left behind)

Use this to verify every Top-25 + add is owned by a phase.

| ID | Feature | Phase(s) | Notes |
|---|---|---|---|
| 1 | Global airline coverage | 0, 1 | Live feed honesty |
| 2 | Real-time flight search | 1 | |
| 3 | Real-time fare & pricing | 1, 2 | Revalidate live + diagnostics |
| 4 | NDC content | 0 gate, **7** | Only if contract |
| 5 | LCC / Direct Connect | 0 gate, **7** | Only if contract |
| 6 | Booking & ticketing | 1, 2 | Ticket # + vault |
| 7 | Multiple payment options | 0 gate, **7** | Razorpay first; expand if needed |
| 8 | Ancillary services | 0 gate, **6** | |
| 9 | Seat map & selection | 0 gate, **6** | |
| 10 | Fare families | 0 gate, **6** | |
| 11 | Promo / private fares | 0 gate, **7** | |
| 12 | Corporate / SME fares | 0 gate, **7** | |
| 13 | Reissue & exchange | **7** | |
| 14 | Cancellation & refund API | **2** | |
| 15 | Fare rules & conditions | **2** | |
| 16 | Multi-source aggregation | **3** | |
| 17 | Smart offer ranking | **3** | |
| 18 | High API performance | 1 (enable), keep | Cache on with live |
| 19 | API security | Keep (baseline) | Harden in 8 for partner keys |
| 20 | Monitoring & analytics | **2**, 3 | |
| 21 | Booking status & notifications | **2**, 7 | Email first; WA Cloud later |
| 22 | Interline / codeshare | **7** | Structured segments |
| 23 | AI & personalization | **7** | L2B-safe |
| 24 | Scalability & reliability | 1, 2 | Load proof |
| 25 | Developer docs & sandbox | 0, 1, **8** | |
| **26** | Global currency | **4** | Your ask |
| **27** | Multilingual | **5** | Your ask |
| 28 | Markup / quote honesty | Keep | All phases respect snapshots |
| 29 | L2B / shopping cache | 1 enable | Already built |
| 30 | White-label | **7** polish | |
| 31 | Commission / wallet | **7** polish | |
| 32 | Document vault | 1 staging smoke | Already built |
| 33 | Hotel parity | **3** | |
| 34 | Offer snapshot immutability | Keep | Sacred in 6+ |
| 35 | Idempotent pay/book | **1** audit/fix | |
| 36 | Supplier health dashboard | **2** | |
| 37 | SSR / special requests | **6** partial | |
| 38 | Schedule change / disruption | **7** | |
| 39 | Audit export | **2** | |
| 40 | Partner / public API | **8** | B2C brand bridge |

---

## Phase 0 — Commercial + capability lock

**Goal:** Know what the first supplier can actually do before we build castles on sand.  
**Duration:** 0.5–1 week · **Depends on:** Sahil + Nilesh (Farhan prepares templates)

### Surfaces

| Surface | Deliverable |
|---|---|
| **Docs / commercial** | Filled supplier capability matrix (which of 4–15, 8–13 exist) |
| **Docs / Phase 0 pack** | Sandbox credentials + L2B contract truth (replace provisional 80/120 if different) |
| **Config** | Decision: first live supplier = TBO **or** TripJack |
| **Ops** | Staging env checklist (Redis, R2, Razorpay test, Sentry) |

### Implement / do

- [ ] Nilesh: pick **primary** live supplier for pilot *(engineering default: TBO)*
- [ ] Sahil: fill `docs/phase-0/SUPPLIER_L2B_CONTRACT.md` (real clauses)
- [ ] Sahil: fill sandbox credential pack
- [x] Capability matrix template: `docs/phase-0/FC_CAPABILITY_MATRIX.md`
- [x] Payment policy note: charge currency for V1 (default INR) vs display-only FX (Phase 4)
- [x] Locale policy note: EN + HI first (Phase 5); other locales later
- [x] Confirm B2B vs B2C split: **B2C out of scope until Phase 8**
- [x] Staging secrets checklist: `docs/ops/FC_STAGING_SECRETS_CHECKLIST.md`
- [x] FC Phase 0 lock: `docs/phase-0/FC_PHASE_0_LOCK.md`

### Acceptance

- [ ] Written primary supplier name *(Nilesh — pending; default TBO)*
- [ ] Capability matrix checked for items that unblock Phases 6–7 *(Sahil)*
- [x] Staging secrets list exists (even if values in password manager)

### Exit

Team can answer: *“What can we sell in the next 90 days without inventing supplier features?”*

### Feature IDs gated

1–15, 26–27 (policy), 4–5/8–13 feasibility for later phases

---

## Phase 1 — Live supplier spine

**Goal:** Real search → revalidate → book → ticket artifact on staging (no more simulated-as-live).  
**Duration:** 1–2 weeks · **Depends on:** Phase 0

### Surfaces

| Surface | Deliverable |
|---|---|
| **Adapter** | Real HTTP client for primary supplier (`search` / `revalidate` / `book` / `cancel` / `status`) |
| **API** | Existing inventory/booking paths work against live sandbox |
| **Agent UI** | Search results show **live** offers (source badge: supplier code); indicative cache badge still honest |
| **Worker** | Confirm job books live; stores PNR + ticket refs |
| **Vault** | Ticket/voucher PDF or document stored in R2/S3 when available |
| **Ops** | `SEARCH_CACHE_ENABLED=true` on staging; vault creds; hosted smoke checklist |
| **Tests** | Contract tests against sandbox or recorded fixtures; idempotency review |

### Implement

- [x] Replace simulated-only TBO path with **live httpx client** gated by `TBO_LIVE_ENABLED` + creds (simulated fallback remains honest)
- [x] Credentials via env (Fernet available for future DB secrets); never commit secrets
- [x] Map supplier errors → TripOS `InventoryRevalidateError` / `AppError` codes
- [x] Persist `supplier_pnr`, `supplier_booking_id`, `ticket_numbers` on booking
- [x] On success: upload ticket document to vault when supplier returns URL
- [x] Ops docs: enable cache + vault on staging (`HOSTED_SMOKE` FC § + secrets checklist)
- [x] Idempotency audit: pay link create + booking confirm (`FC_PHASE1_IDEMPOTENCY_AUDIT.md`)
- [ ] Hosted smoke: search → quote → pay (test) → confirm → booking visible *(blocked on Sahil sandbox keys)*
- [x] Docs: `inventory-v1-mock.md` live/sim honesty + agent source badge

### Acceptance

- [ ] Staging search returns **non-SIMULATED** offers from primary supplier *(needs live creds)*
- [x] Revalidate before pay uses adapter path (live when enabled)
- [ ] Confirmed booking has real/sandbox PNR (or documented sandbox limitation in ops note) *(needs live creds)*
- [x] Cache hit does not meter a look; miss does (L2B Phases already)
- [x] Prod still cannot use `local` document storage
- [x] Pytest: `tests/test_fc_phase1_live_spine.py`

### Exit

Pilot agency can complete one live-sandbox booking end-to-end on staging.

### Feature IDs

**1, 2, 3, 6, 18, 24, 29, 32, 35** (+ keeps 19, 28, 34)

### Likely files / areas

`apps/api/app/adapters/*`, `services/inventory.py`, `services/jobs.py`, `services/payments.py`, `document_storage`, `docs/ops/HOSTED_SMOKE.md`, config/env

---

## Phase 2 — Fare rules + cancel/refund + ops visibility

**Goal:** Money and post-book honesty — agent sees rules; ops sees cancel/refund; health is visible.  
**Duration:** 1–2 weeks · **Depends on:** Phase 1

### Surfaces

| Surface | Deliverable |
|---|---|
| **API** | Fare rules by offer/quote; cancel booking; refund status read model |
| **Agent UI** | Fare rules on quote; cancel booking CTA + status; refund state if any |
| **Admin** | Refund queue / captured-failed; supplier health strip; audit export |
| **Notifications** | Email (or in-app) on booking confirmed / failed (v1) |
| **Ops** | Update refund runbook: guided auto vs manual steps |
| **Data** | Refund status enum; cancel audit events |

### Implement

- [x] `GET`/`POST` fare-rules attached to offer/quote (`/inventory/fare-rules`, `/quotes/{id}/fare-rules`)
- [x] Show change/cancel penalties on quote detail
- [x] Live `adapter.cancel` wired; booking status → cancelled *(already existed; refund auto-request added)*
- [x] Refund record lifecycle: requested → processing → succeeded/failed
- [x] Admin: supplier health (latency p95, error %, circuit) + Failures refunds tab
- [x] Admin/API: audit export `GET /admin/audit/export`
- [x] Notify agent email on confirm success/fail
- [x] Pytest: `tests/test_fc_phase2_ops.py`

### Acceptance

- [x] Agent can open fare rules before pay (quote detail card)
- [x] Agent/ops can cancel a booking and see status
- [x] Admin shows refund state (Failures → Refunds)
- [x] Supplier health visible on admin suppliers + `/admin/suppliers/health`

### Exit

“Pay OK / book fail / cancel / refund” is operable from product + runbook, not tribal knowledge.

### Feature IDs

**14, 15, 20, 21 (partial), 36, 39**

---

## Phase 3 — Aggregation + ranking + hotel parity

**Goal:** Multi-source honesty and usable result quality; hotels not left as orphan mock.  
**Duration:** 1–2 weeks · **Depends on:** Phase 1 (Phase 2 can overlap)

### Surfaces

| Surface | Deliverable |
|---|---|
| **API** | Aggregation with source labels; sort/filter params |
| **Agent UI** | Source badge; sort by price/duration/stops; basic filters |
| **Adapter** | Second supplier **or** proven failover with live primary + mock secondary policy documented |
| **Hotel** | Live or clearly gated hotel search parity checklist |
| **Admin** | Offers-by-supplier counts |

### Implement

- [x] Dedupe/merge strategy v1 (`offer_aggregation.py` — fingerprint → cheapest / preferred)
- [x] Offer fields: `source_type`, `duration_minutes`, `stops`, `airline_*`, `depart_time`
- [x] Ranking: price, duration, stops, recommended (API + client)
- [x] Filters: stops, airlines, max price (API + client-side without re-search)
- [x] Single-supplier waiver: `FC_SINGLE_SUPPLIER_WAIVER.md` (TBO primary; mock+tbo for merge tests)
- [x] Hotel parity write-up: `hotel-parity-status.md` (mock-gated, shared stack)
- [x] Admin last-search offer counts on Suppliers + search response `supplier_counts`
- [x] Pytest: `tests/test_fc_phase3_aggregation.py`

### Acceptance

- [x] Search UI can sort/filter without re-hitting supplier
- [x] Multi-supplier waived/documented; source visible on card (+ source_type)
- [x] Hotel path has written parity status (mock-gated)

### Exit

Agents can compare offers intelligently; inventory strategy is honest.

### Feature IDs

**16, 17, 33**

---

## Phase 4 — Global currency converter

**Goal:** Display and quote honesty in multiple currencies without inventing fares.  
**Duration:** 1–2 weeks · **Depends on:** Phase 1 (can parallel Phase 2–3)  
**Your ask #26**

### Surfaces

| Surface | Deliverable |
|---|---|
| **Data** | FX rates table (`base`, `quote`, `rate`, `as_of`, `source`) |
| **API** | Convert helper; search/quote responses include `display_currency` amounts |
| **Admin** | FX rates manage (manual) + optional provider hook |
| **Agent UI** | Org/user preferred currency; amounts shown converted |
| **Public quote** | Display currency + “rate as of …” footnote |
| **Payments** | **Charge currency policy v1** (default: still INR / settle currency) — display ≠ charge until approved |
| **Snapshot** | Quote stores supplier amount+currency **and** display amount+rate used |

### Implement

- [x] FX service interface + admin CRUD rates (bootstrap)
- [x] Optional: pull from FX API on schedule (feature-flagged)
- [x] Org setting: `preferred_currency`; user override optional
- [x] Search/quote serialization: `money: { currency, amount, display_currency, display_amount, fx_rate, fx_as_of }`
- [x] Rounding policy doc + unit tests
- [x] Razorpay/create pay link still uses settle currency until multi-currency pay approved
- [x] Never mutate supplier fare via FX — convert for display only in v1
- [x] Pytest: conversion math; snapshot stores rate

### Acceptance

- [x] Agency set to USD (or AED) sees converted browse/quote amounts
- [x] Quote PDF/share text shows display currency + rate timestamp
- [x] Payment still succeeds in configured charge currency
- [x] Admin can update rates

### Exit

Global **display** currency works end-to-end; charge-currency expansion is a later commercial toggle (Phase 7 item 7 if needed).

### Feature IDs

**26**

---

## Phase 5 — Multilingual (i18n)

**Goal:** Agent + traveler-facing surfaces work in EN + HI (extensible).  
**Duration:** 1–2 weeks · **Depends on:** Phase 1; best after/with Phase 4 for number formats  
**Your ask #27**

### Surfaces

| Surface | Deliverable |
|---|---|
| **Data** | `org.default_locale`, `user.locale` |
| **Agent UI** | next-intl (or equivalent) message catalogs EN/HI |
| **Public quote** | Localized strings + locale-aware dates |
| **API** | `Accept-Language` or `locale` query; localized `AppError` messages |
| **WhatsApp / email templates** | Locale-specific copy |
| **AI** | Locale passed into copilot |
| **Admin** | Locale can stay EN-first (optional HI later) |

### Implement

- [x] Locale enum: `en`, `hi` (+ fallback `en`)
- [x] Wire org/user locale settings UI
- [x] Extract agent + public quote strings to catalogs
- [x] Error code → message map per locale
- [x] Format dates/numbers via `Intl` + Phase 4 currency
- [x] WhatsApp quote share template per locale
- [x] AI: include locale in system/user prompt
- [x] Checklist: no hardcoded English on quote pay page

### Acceptance

- [x] Switch org to `hi` → agent shell + public quote render Hindi
- [x] API error in HI when locale set
- [x] Currency + dates format correctly per locale

### Exit

EN/HI product surfaces are real; adding a third locale is catalog work, not a rewrite.

### Feature IDs

**27** (+ improves 21 templates)

---

## Phase 6 — Fare families + ancillaries + seats

**Goal:** Sell branded fares and extras inside TripOS (when supplier supports).  
**Duration:** 2–4 weeks · **Depends on:** Phase 0 capability = yes; Phase 1–2 done

### Surfaces

| Surface | Deliverable |
|---|---|
| **Schema** | Fare family on offer; ancillary catalog; seat map DTO; quote line-items |
| **API** | Fare families in search; `GET` seat map; add/remove ancillary on quote; revalidate with extras |
| **Agent UI** | Family compare; seat picker; baggage/meal select; updated total |
| **Book path** | Book payload includes selected ancillaries/seats |
| **Snapshot** | Line-items frozen on quote (immutability preserved) |

### Implement

- [x] Extend `NormalizedOffer` with `fare_family`, `cabin`, structured baggage summary
- [x] Search UI: group/compare Basic vs Flex vs Premium when present
- [x] Ancillary APIs: list available extras for offer
- [x] Seat map API + UI selection → hold/attach to quote
- [x] Quote total = base + ancillaries; revalidate must include selection
- [x] SSR codes (wheelchair etc.) as optional special requests if supplier allows
- [x] Mock adapter fixtures for families/ancillaries so UI can develop offline
- [x] Pytest: quote with seat; revalidate failure clears stale seat

### Acceptance

- [x] Agent can sell a higher family and add seat/baggage without leaving TripOS
- [x] Confirmed booking reflects ancillaries in snapshot/docs
- [x] If supplier lacks capability: feature flagged off cleanly (no broken UI)

### Exit

Rich offer selling works on at least one live-capable path (or supplier-flagged).

### Feature IDs

**8, 9, 10, 37 (partial)**

---

## Phase 7 — Servicing + richer content + B2B polish

**Goal:** Post-booking servicing and optional richer inventory; polish B2B monetization.  
**Duration:** 2–4 weeks · **Depends on:** Phase 2; Phase 0 gates for NDC/LCC/promo

### Surfaces

| Surface | Deliverable |
|---|---|
| **API** | Reissue/exchange quote → confirm; promo/corp deal codes; structured segments |
| **Agent UI** | Change booking flow; enter deal code; segment display (marketing vs operating) |
| **Notifications** | Stronger status + optional WhatsApp Cloud; schedule-change alert when available |
| **Admin** | Commission statements; white-label DNS checklist complete |
| **Adapters** | NDC/LCC only if contracted — new source_type paths |
| **AI** | Preference memory + ranked suggestions (cache-safe) |
| **Payments** | Extra methods only if commercial requires |

### Implement

- [x] Reissue: request change → supplier price diff → collect → confirm
- [x] Org settings: private/promo/corporate codes → passed on search
- [x] Segment model: origin/dest/dep/arr, marketing carrier, operating carrier, flight #
- [x] Schedule change ingest (webhook or poll) → notify agent
- [x] NDC/LCC adapter hooks **only if** Phase 0 said yes *(gated OFF — matrix pending)*
- [x] White-label: production custom domain verify
- [x] Commissions: settle statement export
- [x] AI personalization v1 (opt-in)
- [x] Payment expansion gated by Nilesh *(waived — no commercial ask)*

### Acceptance

- [x] At least one post-booking change path works in sandbox **or** waived with manual SOP still linked *(mock quote/confirm + SOP hint; not live PNR rewrite)*
- [x] Codeshare/segments display correctly when supplier sends them *(mock + TBO mapper)*
- [x] Commission + white-label polish checklist signed *(API/checklist shipped; commercial sign-off table still pending)*

### Exit

B2B product is “serviceable” beyond new bookings; richer content is onboarded without redesigning the OS.

### Feature IDs

**4, 5, 7, 11, 12, 13, 22, 23, 30, 31, 38** (+ 21 complete)

---

## Phase 8 — Partner / B2C-facing API

**Goal:** Separate B2C brand (or external partners) consumes TripOS B2B APIs safely — **no shared B2C codebase inside TripOS**.  
**Duration:** 2–3 weeks · **Depends on:** Phases 1–5 minimum; 6–7 recommended

### Surfaces

| Surface | Deliverable |
|---|---|
| **API** | Versioned partner API (`/v1/partner/...` or gateway) with API keys |
| **Auth** | Partner app credentials; scoped org/tenant; rate + L2B quotas |
| **Webhooks** | booking.confirmed / failed / cancelled / refund.updated |
| **Docs** | Public OpenAPI + sandbox guide + Postman |
| **Admin** | Partner apps CRUD; usage + L2B per partner |
| **Security** | Key rotation; IP allowlist optional; no agent-JWT sharing with B2C |

### Implement

- [x] Partner authentication (API key / OAuth client credentials) *(API key; OAuth client-credentials deferred)*
- [x] Expose: search, revalidate, quote create, pay-link create (or pay status), booking status, cancel
- [x] Enforce L2B + rate limits **per partner**
- [x] Webhooks with signed payloads
- [x] Sandbox partner tenant + seed docs
- [x] Explicit non-goals doc: reviews, B2C catalog SEO, consumer social — **belong in B2C product**, not TripOS

### Acceptance

- [x] External client (Postman) completes sandbox book via partner API alone *(API + Postman + HTTP me/search tests; full pay→book still needs mock payment + worker)*
- [x] B2C team can integrate without DB access to TripOS
- [x] Abuse by one partner cannot silently burn platform L2B without brakes *(org L2B + Redis/memory partner rate limit)*

### Exit

**B2B ↔ B2C bridge is real.** Two companies stay separate; APIs are the contract.

### Feature IDs

**25, 40** (+ hardens 19)

---

## 3. Board checklist

### Phase 0
- [x] Capability matrix + staging secrets templates + policy locks
- [ ] Primary supplier chosen by Nilesh + Sahil matrix values
- [ ] L2B contract truth + sandbox keys in secrets/

### Phase 1
- [x] Live TBO httpx client + simulated fallback + BookResult + ticket refs migration
- [x] Vault hook for ticket URL + agent source badge + idempotency audit
- [ ] Staging E2E book with `TBO_LIVE_ENABLED=true` (Sahil credentials)

### Phase 2
- [x] Fare rules API/UI
- [x] Cancel + refund lifecycle + admin queue
- [x] Supplier health + audit export + booking emails

### Phase 3
- [x] Dedupe + ranking/filters + source fields
- [x] Single-supplier waiver + hotel parity status
- [x] Admin/search supplier offer counts

### Phase 4
- [x] FX + display currency on search/quote/pay footnote
- [x] Snapshot stores rate

### Phase 5
- [x] EN/HI agent + public quote
- [x] Localized API errors + templates

### Phase 6
- [x] Fare families + ancillaries + seat map (or cleanly flagged off)

### Phase 7
- [x] Reissue and/or richer content per contract
- [x] White-label + commission polish
- [x] Notifications/schedule-change as available

### Phase 8
- [x] Partner API + webhooks + sandbox docs (B2C bridge)

---

## 4. Explicit non-goals (entire FC plan)

| Out of scope here | Where it belongs |
|---|---|
| B2C storefront, reviews, traveler UGC | Separate B2C company |
| Building our own GDS | Never |
| BSP/IATA settlement inside TripOS | Commercial / later |
| Perfect NDC before live TBO/TripJack works | Phase 7 only if contracted |
| Multi-currency **collection** before gateway + commercial approve | After Phase 4 display FX |
| Merging B2B and B2C codebases | Forbidden — use Phase 8 APIs |

---

## 5. Start here

1. Run **Phase 0** with Nilesh/Sahil (capability matrix).  
2. Say **“Start FC Phase 1”** (or Phase 0 if commercial docs still empty) to begin engineering.  
3. Keep [`flight-api-features-gap-plan.md`](./flight-api-features-gap-plan.md) as the narrative for sir; **this file is the build checklist**.

---

*Single source of truth for Flight Commerce execution. Update checkboxes as phases close.*
