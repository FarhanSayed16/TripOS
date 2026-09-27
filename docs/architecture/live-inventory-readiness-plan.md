# TripOS — Live Inventory Readiness Plan  
### Look-to-Book search cache **+** must-fix hardening (unified phases)

**Status:** Execution plan (2026-09-25) — **Phase 0–7 engineering CLOSED** · next: hosted smoke + Sahil contract truth before heavy live  
**Owners:** Farhan (build) · Sahil (supplier contract) · Nilesh (conversion / pilot)  
**Detail refs:**  
- **Conceptual (why / logic / impact)** → [`live-inventory-phases-0-7-explained.md`](./live-inventory-phases-0-7-explained.md)  
- L2B theory → [`look-to-book-search-cache-plan.md`](./look-to-book-search-cache-plan.md)  
- Longer risk catalog → [`travel-tech-hardening-suggestions.md`](./travel-tech-hardening-suggestions.md) (trimmed; use this file to build)  
- Phase 0 contract pack → [`../phase-0/SUPPLIER_L2B_CONTRACT.md`](../phase-0/SUPPLIER_L2B_CONTRACT.md)

**Rule:** Work **one phase at a time**. Each phase has concrete files, acceptance tests, and can ship independently.

---

## 0. Only the important problems (ignore the rest for now)

| # | Problem | Why it matters | TripOS today |
|---|---|---|---|
| **1** | Live search on every browse → bad **L2B** / feed cutoff | Supplier kills or bills you | No shopping cache |
| **2** | Price moves between browse and pay | Money + trust | Revalidate exists; FE delta weak |
| **3** | Pay captured / book failed | Real money stuck | SOP exists; need metric + audit discipline |
| **4** | One org hammers search | Ruins platform L2B | 30/min org limit only |
| **5** | Ticket PDFs on ephemeral disk | Data loss in prod | Local blocked; R2 not wired |
| **6** | AI → live search | Explodes L2B | AI default off; must stay cache-only |

Everything else (NDC merge, WhatsApp Cloud API, compensate multi-item cancel, auto-settle commissions, separate `apps/ai`) → **later / backlog**. Do not block these phases.

---

## 1. Target architecture (both plans together)

```text
                    ┌─────────────────────────────┐
  Agent search ───► │ Redis shopping cache (route) │──hit──► indicative offers + age
                    └──────────────┬──────────────┘
                                   │ miss / refresh worker
                                   ▼
                         Live supplier search
                                   │
                                   ▼
                         Quote (OfferSnapshot)
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     wa.me / browse         Create pay link        Confirm job
     (no live)              REVALIDATE (live)      REVALIDATE → BOOK
                                   │                    │
                                   ▼                    ▼
                            fare_changed UI      Booking + supplier_code
                            or payment OK         + L2B counters++
```

**Shopping** = cache. **Money** = always live revalidate (already in `payments.py` + `jobs.py`).

---

## 2. Unified phase plan

### Phase 0 — Contract facts (0.5–1 day, Sahil) — **ENGINEERING CLOSED 2026-09-25**

**Goal:** Know what “look” means before coding numbers.

**Do:**
- [x] Questionnaire + provisional defaults: [`docs/phase-0/SUPPLIER_L2B_CONTRACT.md`](../phase-0/SUPPLIER_L2B_CONTRACT.md)
- [x] Sandbox pack L2B section + decisions log L2B block
- [x] Env placeholders: `L2B_WARN_RATIO` / `L2B_CRITICAL_RATIO` / `SEARCH_CACHE_*` in `apps/api/.env.example`
- [ ] Sahil fills real TBO/TripJack clauses (non-blocking for Phase 1 build; **blocking for heavy live prod search**)

**Exit:** Team knows warn/critical L2B targets (even if provisional).  
**Locked provisional:** warn **80** · critical **120** · looks = live `search` + `revalidate` · assume no shopping API until confirmed.

---

### Phase 1 — Measure live calls + L2B (2–3 days) — **DONE 2026-09-25**

**Goal:** See the problem before optimizing it.

#### Implement

1. **New service** `apps/api/app/services/supplier_usage.py`
   - `record_live_call(supplier_code, kind, source, org_id=None)`  
     `kind`: `search` | `revalidate` | `book` | `confirmed`  
     `source`: `user_search` | `ai_search` | `payment_revalidate` | `confirm_revalidate` | `quote_refresh` | …
   - Persist to table `supplier_usage_daily`

2. **Alembic migration** — `b3c4d5e6f7a8_add_supplier_usage_daily.py`

3. **Wire calls**
   - `inventory.py` — every live `adapter.search` / revalidate / book
   - `payments.py` / `jobs.py` / `quotes.py` / `ai.py` — with source tags
   - On booking confirmed — increment `confirmed_bookings`

4. **Admin** — `GET /admin/analytics` includes `l2b_7d`; `GET /admin/l2b?days=7`

5. **Config** — `L2B_WARN_RATIO` / `L2B_CRITICAL_RATIO` on Settings

#### Acceptance
- [x] Metering wired on search / revalidate / book / confirmed
- [x] Admin shows rolling 7-day L2B
- [x] Pytest: `tests/test_supplier_usage.py`

#### Files
`app/services/supplier_usage.py`, `app/services/inventory.py`, `payments.py`, `jobs.py`, `app/api/admin.py`, `alembic/versions/b3c4d5e6f7a8_…`, `tests/test_supplier_usage.py`

---

### Phase 2 — Redis shopping cache MVP (3–5 days)  ★ L2B core — **DONE 2026-09-25**

**Goal:** Same route searched by many agents → **one** live search within TTL.

#### Implement

1. **Redis client** `apps/api/app/core/redis_client.py` — `get_json` / `set_json` / `try_lock` / `release_lock`
2. **Cache module** `apps/api/app/services/search_cache.py` — route key + singleflight
3. **`search_inventory`** — cache hit skips live + L2B meter; miss → live → set
4. **Config** — `SEARCH_CACHE_ENABLED` / `SEARCH_CACHE_TTL_SECONDS` on Settings (default off)
5. **API** — `SearchResponse.cache_hit` + `cache_age_seconds`
6. **FE** — Indicative badge on agent search results
7. **Singleflight** — Redis `SET NX EX 5` on `key:lock`

#### Acceptance
- [x] Same query ×10 within TTL → ≤1 adapter.search (`tests/test_search_cache.py`)
- [x] Cache miss still returns offers
- [x] Redis down → log + fall through to live (fail-open lock)

#### Files
`app/core/redis_client.py`, `app/services/search_cache.py`, `app/services/inventory.py`, `app/schemas/inventory.py`, `apps/web/.../search/*`, `tests/test_search_cache.py`

---

### Phase 3 — Fare-change UX + money safety (2–4 days)  ★ Hardening musts #2–3 — **DONE 2026-09-25**

**Goal:** When revalidate fails at pay, agent/customer understands; ops can see pay/book gap.

#### Implement

1. **API** — `FARE_CHANGED` includes `previous_total_paise` / `new_total_paise` (AppError details)
2. **FE** — quote detail modal: Accept new fare → refresh → new quote; Stay on quote
3. **Metric** — `payment_captured_booking_failed_7d` on admin analytics (+ FE card)
4. **Guardrail** — pytest: revalidate failure blocks pay link (`test_phase3_fare_change.py`)
5. **Quote TTL** — `QUOTE_FLIGHT_TTL_HOURS` / `QUOTE_HOTEL_TTL_HOURS` (default 4 / 12)

#### Acceptance
- [x] E2E `test_fare_change_blocks_payment` asserts amount fields (run with DB)
- [x] FE modal path for FARE-CHG offers
- [x] Admin shows captured-but-failed count

#### Files
`inventory_errors.py`, `exceptions.py`, `payments.py`, `quotes.py`, `mock_adapter.py`, `admin.py`, quote FE, `tests/test_phase3_fare_change.py`

---

### Phase 4 — Per-org L2B brakes + AI guard (2–3 days)  ★ Hardening #4 + #6 — **DONE 2026-09-25**

**Goal:** One bad agency (or AI) cannot burn the supplier feed.

#### Implement

1. **`supplier_usage_daily_org`** + migration `c4d5e6f7a8b9`
2. **Live-search policy** after cache miss: `block` (429 `SEARCH_THROTTLED_L2B`) / `cache_only` / `allow`
3. **Config:** `L2B_THROTTLE_MIN_CONFIRMED`, `L2B_ORG_CACHE_ONLY`, `L2B_AI_BLOCK_ON_CRITICAL`
4. **AI** — `ai_search` blocked when org or platform L2B critical; AppError rethrown (not 502)
5. **Admin** — `GET /admin/l2b/orgs` + analytics “Org L2B offenders” table

#### Acceptance
- [x] Org with huge searches / 0 books → `block` in pytest
- [x] AI blocked under critical
- [x] Pytest: `tests/test_phase4_l2b_org.py`

#### Files
`supplier_usage.py`, `inventory.py`, `api/ai.py`, `api/admin.py`, config, migration, admin analytics FE, tests

---

### Phase 5 — Background cache refresh (3–5 days)  ★ L2B scale — **DONE 2026-09-25**

**Goal:** Hot routes stay warm without depending on user traffic.

#### Implement

1. **Popularity** — `search_popularity.get_popular_routes` from `search_requests.payload` (7d top N)
2. **Worker** — periodic `refresh_hot_routes` + outbox handler `inventory_cache_refresh`
3. **TTL bands** — hot / warm / default via `set_offers(..., band=)`
4. **Ops** — pause with `SEARCH_CACHE_REFRESH_ENABLED=false` (Phase 39 checklist)

#### Acceptance
- [x] Refresh runs with zero UI when enabled (worker interval)
- [x] Circuit-open suppliers skipped; live calls metered as `cache_refresh`
- [x] Pytest: `tests/test_phase5_cache_refresh.py`

#### Files
`search_popularity.py`, `cache_refresh.py`, `search_cache.py`, `worker.py`, config, `PHASE_39_CHECKLIST.md`, tests

---

### Phase 6 — Document vault (R2/S3) (3–5 days)  ★ Hardening #5 — **DONE 2026-09-25**

**Goal:** Real tickets/vouchers safe in production.

#### Implement

1. **`document_storage.py`** — local + boto3 S3/R2 put/get/delete/presign
2. **`documents.py`** — real upload for s3/r2 (no more 501); download streams or `?redirect=true` presign
3. **Prod guard** — `ENV=production` + `local` → **503** (unchanged)
4. **Share-link** wa.me helper kept
5. **Ops** — `HOSTED_SMOKE.md` vault section + `.env.example` keys

#### Acceptance
- [x] Object upload path wired (staging: set R2 creds + smoke upload/download)
- [x] Prod with `local` still 503
- [x] Pytest: `tests/test_phase6_document_vault.py`

#### Files
`app/services/document_storage.py`, `app/api/documents.py`, `.env.example`, `docs/ops/HOSTED_SMOKE.md`, `pyproject.toml`

---

### Phase 7 — Survival controls (2 days) — **DONE 2026-09-25**

**Goal:** Auto soft-brake when platform L2B goes critical.

#### Implement

1. On critical global L2B:
   - Multiply TTL by 2 automatically (cap e.g. 15 min)
   - Pause Phase 5 refresher for warm/cold routes
2. Admin banner + Sentry alert
3. Runbook section in L2B doc / Phase 39 checklist

#### Acceptance
- [x] Unit: critical counters → TTL widen + warm refresh skip (`tests/test_phase7_l2b_survival.py`)
- [ ] Staging: fake critical counters → TTL widen logged + refresher pause (ops verify)

#### Files
`app/services/l2b_survival.py`, `search_cache.py`, `cache_refresh.py`, `inventory.py`, `admin.py`, admin layout/analytics FE, `docs/ops/L2B_SURVIVAL_RUNBOOK.md`, `.env.example`

---

## 3. Suggested calendar (parallel-friendly)

| Week | Phase | Focus |
|---|---|---|
| 0 | Phase 0 | Sahil contract (parallel anytime) |
| 1 | Phase 1 | Counters + admin L2B |
| 1–2 | Phase 2 | Redis shopping cache ← **main L2B win** |
| 2 | Phase 3 | Fare-change UX + pay/book metric |
| 2–3 | Phase 4 | Per-org throttle + AI guard |
| 3 | Phase 5 | Background refresh |
| 3–4 | Phase 6 | R2 vault (can parallel with 5 if two streams) |
| 4 | Phase 7 | Auto survival brakes |

**Two-stream option:** Farhan A = Phases 1→2→5→7 (L2B). Farhan B / later = Phases 3→4→6 (hardening). Merge before live supplier production traffic.

---

## 4. Definition of done (live supplier ready)

Ship live TBO/TripJack to pilot agents only when:

- [x] Phase 0 clauses known (provisional; Sahil override before heavy live)  
- [x] Phase 1 L2B visible  
- [x] Phase 2 cache on in staging with proof (≤1 live / TTL window) — **code done; enable `SEARCH_CACHE_ENABLED=true` + Redis in staging**  
- [x] Phase 3 fare-change path usable  
- [x] Phase 4 org throttle exists  
- [x] Phase 6 vault not on local disk in prod — **code: prod+local → 503; wire R2 creds in staging**  
- [x] Phase 7 survival soft-brakes (TTL ×2 + warm refresh pause + admin banner) — **code done; staging sim optional**  
- [ ] Hosted smoke + commercial gates (Sprint P) still required for GO V2  

Phase 5 + 7 strongly recommended before heavy marketing traffic.

---

## 5. Explicitly deferred (do not mix into these phases)

- Compensate cancel multi-item  
- WhatsApp Cloud API  
- Separate `apps/ai` service  
- Auto-settle commissions  
- Full NDC/LCC merge/dedupe  
- Orphan PNR reconcile job (nice; add after Phase 3 if time)  
- DNS white-label production verify  

Track in `backlog.md` / shortened hardening doc.

---

## 6. Board checklist

### Phase 0
- [x] Supplier L2B / shopping API pack + provisional warn/critical locked (`SUPPLIER_L2B_CONTRACT.md`)
- [ ] Sahil replaces provisional with contract truth (before heavy live)

### Phase 1
- [x] `supplier_usage` + admin L2B

### Phase 2
- [x] Redis search cache + FE indicative badge

### Phase 3
- [x] Fare-change UX + captured-failed metric + configurable quote TTL

### Phase 4
- [x] Per-org L2B throttle + AI cache/guard

### Phase 5
- [x] Background hot-route refresh

### Phase 6
- [x] R2/S3 document vault

### Phase 7
- [x] Global L2B auto soft-brakes + runbook

**This file is the single phase-wise build plan for L2B + critical hardening.** Use the two companion docs for background only.
