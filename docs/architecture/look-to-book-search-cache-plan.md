# TripOS — Look-to-Book (L2B) & Search Cache Implementation Plan

**Status:** Approved direction (2026-09-25) — detail / theory for L2B  
**Execution plan (phases + hardening merged):** **[`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md)** ← **build from that file**  
**Owners:** Farhan (engineering) · Sahil (supplier contract clauses) · Nilesh (commercial conversion levers)  
**Related:** `architecture/inventory-v1-mock.md`, `multi-supplier-honesty.md`, `ops/PHASE_39_CHECKLIST.md`, Phase 12/25/39 master-plan items  

> **Note:** Section 5 phased checklist below is superseded for day-to-day execution by `live-inventory-readiness-plan.md` (Phases 0–7). Keep this doc for problem framing and cache-key design detail.

---

## 1. Problem statement

Travel supplier APIs (TBO, TripJack, Amadeus, Sabre, etc.) charge money and enforce contracts on **search / shopping traffic**, not only on bookings.

If TripOS does:

```text
1 agent search → 1 live supplier API call
```

then at scale:

- API cost and rate limits explode with concurrent agents
- **Look-to-Book ratio (L2B)** worsens (many looks, few books)
- Suppliers may throttle, bill overages, or **terminate the feed** if monthly booking volume / L2B targets are missed

Industry name: **Look-to-Book Ratio (LTBR / L2B)**.

Typical metric (confirm exact definition in each supplier contract):

```text
L2B = live_supplier_calls ÷ confirmed_bookings   (rolling 7 / 30 days)
```

“Looks” usually include live search and sometimes revalidate/pricing calls — **get the contract wording in writing**.

---

## 2. Core design principle

**Do not treat “browse search” as one user = one live call.**

| Tier | When | Hits live supplier? | Purpose |
|---|---|---|---|
| **Shopping** | Agent browses / compares / AI draft explore | Prefer **cache** (or supplier shopping API) | Fast UX, protect L2B |
| **Re-price** | Intent: send quote / create pay link / book | **Always live** (revalidate) | Guaranteed bookable price |

TripOS **already has the re-price tier** (revalidate before payment link + before confirm job).  
This plan adds the **shopping cache + L2B control plane**.

```text
[Agent search]
      │
      ▼
 Redis route cache ──hit──► return offers (indicative)
      │ miss
      ▼
 Live supplier search ──► fill cache ──► return
      │
      ▼
 Agent builds quote (snapshot)
      │
      ▼
 Revalidate (live) ──► pay link / offline pay
      │
      ▼
 Revalidate (live) ──► adapter.book ──► PNR
```

---

## 3. What already exists in TripOS

| Capability | Location | Status |
|---|---|---|
| Live search orchestration | `app/services/inventory.py` | Every search hits adapters |
| Org search rate limit | `app/core/rate_limit.py` (30/min/org) | Protects TripOS, **not** supplier L2B |
| Revalidate before pay | `app/services/payments.py` | Done |
| Revalidate before book | `app/services/jobs.py` | Done |
| Redis provisioned | `render.yaml` `tripos-redis` | Unused by app today |
| Search cache ADR | `architecture/inventory-v1-mock.md` | Was “skipped for pilot” — **superseded for live suppliers by this plan** |
| `search_requests` audit table | inventory models | Can feed popularity / analytics |

---

## 4. Target architecture (detail)

### 4.1 Cache key (route-based, not user-based)

```text
{supplier}|{type}|{origin}|{dest}|{dep}|{ret}|{cabin}|{adults}|{children}|{infants}|{currency}
```

Example: `mock_supplier|flight|DEL|BOM|2026-10-12||Y|1|0|0|INR`

Rules:

- Same route from 1,000 agents → **one** cache entry (or one per supplier in the key)
- If contract forbids cross-org sharing of offers, prefix with `org_id` (default: shared shopping cache is OK for public fares; private/net fares may need org scoping)

### 4.2 TTL policy (popularity bands)

| Band | Example | Refresh TTL |
|---|---|---|
| Hot | Top routes by 7-day search volume | 60–120 seconds |
| Warm | Occasional but repeating | 5–10 minutes |
| Cold | Rare OD/date | 15–30 minutes **or** miss-only (no background refresh) |

Do **not** design for sub-second browse freshness. Real fare class shifts are minutes-scale for shopping; second-scale accuracy matters at **re-price**.

### 4.3 Background refresh worker

- New outbox/job type or dedicated loop: `inventory_cache_refresh`
- Input: top N keys from `search_requests` / cache hit counters
- Independent of concurrent UI traffic → 10 or 10,000 agents on DEL→BOM cost roughly the **same** live volume for that route
- Respect circuit breaker + `INVENTORY_SUPPLIERS` + `SUPPLIER_STRATEGY`

### 4.4 Re-price tier (keep / harden)

Existing gates must stay mandatory for live money:

1. Create payment link → revalidate  
2. Confirm job → revalidate → book  

Optional UX: “Lock fare / refresh price” before WhatsApp send.

UI copy: *“Prices while browsing are indicative. Final fare confirmed before payment.”*

### 4.5 L2B control plane

Counters (per supplier + global), increment on:

- `search` live miss / background refresh  
- `revalidate`  
- `book`  
- `booking.confirmed` (denominator)

Admin:

- Rolling 7d / 30d L2B  
- Alert thresholds vs contractual max (config)  
- Soft levers: widen TTL, pause cold refresh, disable AI→live search

---

## 5. Phased implementation plan

### Phase 0 — Contract lock (before live API keys in production)

**Owner:** Sahil + Farhan  

Deliverables:

- [ ] Written definition of what counts as a “look” / “search” / “pricing call”
- [ ] Maximum L2B or minimum bookings/month (if any)
- [ ] Whether a **shopping / fare-cache / Instant Search** API exists that does **not** count (or counts cheaper) vs bookable pricing
- [ ] Store answers in `secrets/` pack + summary note in Phase 0 decisions

**Exit:** No ambiguity on what we must optimize.

---

### Phase A — Instrumentation (1–3 days)

**Owner:** Farhan  

Deliverables:

- [ ] Structlog + DB/metrics counters: `supplier_live_search`, `supplier_revalidate`, `supplier_book`, `booking_confirmed`
- [ ] Tag each with `supplier_code`, `org_id` (optional), `source` (`user_search` | `cache_refresh` | `payment_revalidate` | `confirm_revalidate` | `ai_search`)
- [ ] Admin analytics strip or `/admin/analytics` fields: rolling L2B
- [ ] Unit tests for counter increments on mock adapter path

**Exit:** Can answer “how many live calls per confirmed booking this week?” on mock/staging.

**Files (expected):**

- `app/services/inventory.py`, `payments.py`, `jobs.py`
- `app/api/admin.py` analytics
- `docs/ops/PHASE_39_CHECKLIST.md` (link L2B metric)

---

### Phase B — Shopping cache MVP (3–7 days)

**Owner:** Farhan  

Deliverables:

- [ ] Redis client wired (`REDIS_URL` already in config)
- [ ] `SEARCH_CACHE_ENABLED` (default `false` until staging proof; `true` for live suppliers)
- [ ] `SEARCH_CACHE_TTL_SECONDS` default e.g. `120`
- [ ] In `search_inventory`: get → on miss live search → set
- [ ] Response metadata: `cache_hit`, `cache_age_seconds` (for FE badge)
- [ ] Agent UI: “Indicative · updated Xm ago”
- [ ] Pytest: hit path does not call adapter twice for same key
- [ ] Update `architecture/inventory-v1-mock.md` — cache required for live

**Exit:** Repeated identical searches in staging produce 1 live call within TTL.

**Non-goals in B:** popularity TTL, background refresh, AI changes.

---

### Phase C — Popularity + background refresh (3–7 days)

**Owner:** Farhan  

Deliverables:

- [ ] Aggregate top keys from `search_requests` (last 7 days)
- [ ] Config: `SEARCH_CACHE_HOT_TTL`, `SEARCH_CACHE_WARM_TTL`, `SEARCH_CACHE_TOP_N`
- [ ] Worker job refreshes top N on interval
- [ ] Skip refresh when circuit open / supplier disabled
- [ ] Ops runbook: how to pause refresher if L2B spikes

**Exit:** Hot route live call rate roughly flat vs concurrent agent count.

---

### Phase D — L2B survival controls (2–5 days) — **DONE in live-inventory Phase 7**

**Owner:** Farhan (+ Nilesh for conversion process)  

Deliverables:

- [x] Config: `L2B_WARN_RATIO`, `L2B_CRITICAL_RATIO` + `L2B_SURVIVAL_*`
- [x] Alerts (Sentry / admin banner) at critical
- [x] Auto soft response at critical: TTL ×2 (cap), pause warm refreshes
- [x] Kill switch: AI blocked on critical (Phase 4) + survival brakes
- [x] Runbook: `docs/ops/L2B_SURVIVAL_RUNBOOK.md`
- [ ] Playbook: push follow-ups / quote conversion (ops, not more searches) — Nilesh

**Exit:** Documented runbook + unit tests; staging simulation optional before heavy live.

---

### Phase E — Supplier shopping tier (when available)

**Owner:** Sahil + Farhan  

Deliverables:

- [ ] Wire cheaper shopping endpoint for browse if contract offers it
- [ ] Keep bookable/revalidate/book on pricing APIs
- [ ] Honesty labels in admin suppliers UI

**Exit:** Browse traffic prefers shopping API; re-price still bookable API.

---

## 6. Configuration reference (proposed)

```env
# Phase B+
SEARCH_CACHE_ENABLED=false
SEARCH_CACHE_TTL_SECONDS=120
SEARCH_CACHE_HOT_TTL_SECONDS=90
SEARCH_CACHE_WARM_TTL_SECONDS=600
SEARCH_CACHE_TOP_N=50
SEARCH_CACHE_REFRESH_INTERVAL_SECONDS=60

# Phase D — example only; set from real contract
L2B_WARN_RATIO=80
L2B_CRITICAL_RATIO=120
```

Redis: reuse `REDIS_URL` (Render Blueprint already has `tripos-redis`).

---

## 7. Testing & acceptance

| Phase | Test |
|---|---|
| A | Counters move on search/revalidate/book; admin shows ratio |
| B | Same query ×10 → ≤1 live search inside TTL |
| C | With 0 UI traffic, hot keys still refresh; live count ≈ top_N / interval |
| D | Forced high L2B → warn banner + TTL widen |
| E2E | Happy path still: search → quote → pay → revalidate → book |

Do **not** claim Phase 25 live supplier exit without Phase A+B at minimum.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Stale browse price shocks customer | Clear “indicative” copy + mandatory revalidate before pay |
| Private/net fares leaked across orgs | Org-scoped cache keys when needed |
| Cache stampede on miss | Singleflight / lock per key |
| AI Copilot explodes L2B | Default AI off; AI search must use cache path; never invent prices |
| Redis down | Fail open to live search with loud metric (or fail closed if L2B critical) |

---

## 9. Sequencing vs other TripOS work

1. **Before** production live TBO/TripJack: Phase 0 + A + B  
2. **With** early live traffic: C + D  
3. **Parallel:** Nilesh conversion (pilot, follow-ups) improves denominator (bookings), not only numerator (looks)  
4. Hosted smoke / commercial sign-off remain Sprint P blockers for GO V2 — this plan does not replace them  

---

## 10. Checklist (copy to board)

### Phase 0
- [ ] Supplier L2B / shopping-API clauses written down

### Phase A
- [ ] Live-call counters + admin L2B strip

### Phase B
- [ ] Redis shopping cache MVP + FE indicative badge

### Phase C
- [ ] Popularity TTL + background refresher

### Phase D
- [ ] Alerts + soft brakes + AI guard

### Phase E
- [ ] Native supplier shopping tier (if offered)

**This document is the source of truth for TripOS search-cost / L2B work until phases above are closed.**
