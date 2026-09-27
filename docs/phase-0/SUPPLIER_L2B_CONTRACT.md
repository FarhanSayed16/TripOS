# Supplier L2B / Look-to-Book contract pack (Live Inventory Phase 0)

**Purpose:** Lock what counts as a “look,” ratio limits, and shopping-API options **before** TripOS meters L2B or turns on live search cache.  
**Filled by:** Sahil (primary) · Nilesh (commercial) · Farhan (records engineering defaults)  
**Copy filled answers to:** `secrets/01-supplier-sandbox.md` (never commit secrets)  
**Execution plan:** `docs/architecture/live-inventory-readiness-plan.md` Phase 0  

**Status (2026-09-25):** **Engineering Phase 0 CLOSED** with provisional defaults below. Sahil must replace brackets with contract truth when supplier is chosen.

---

## 1. Supplier identity

| Field | Answer |
|---|---|
| First live supplier | `[ TBO / TripJack / Other: ___ ]` |
| Environment for pilot | `[ sandbox only / sandbox then prod ]` |
| Contract / rate card date | `________` |
| Sahil contact at supplier | `________` |

---

## 2. What counts as a “look” (critical)

Check all that apply per **written** contract (not sales talk):

| Call type | Counts toward L2B / search quota? | Notes |
|---|---|---|
| Flight search / shopping | `[ Yes / No / Cheaper tier ]` | |
| Hotel search | `[ Yes / No / N/A ]` | |
| Revalidate / fare quote / pricing | `[ Yes / No / Separate quota ]` | |
| Book / ticket | `[ Usually no — confirm ]` | |
| Cancel / status | `[ Yes / No ]` | |
| Cached results we never call them for | N/A (our side) | Does not hit supplier |

**Exact contractual definition of L2B (paste or paraphrase):**

```
[ paste ]
```

---

## 3. Limits & penalties

| Item | Answer |
|---|---|
| Max L2B (looks per book) allowed | `[ e.g. 100:1 / 500:1 / not stated ]` |
| Measurement window | `[ calendar month / rolling 30d / other ]` |
| Minimum bookings / month (if any) | `[ e.g. 50 / none ]` |
| Soft throttle before hard cut | `[ Yes — describe / No ]` |
| Overage pricing | `[ Yes — rate / No ]` |
| Termination clause if target missed | `[ Yes — summarize / No / Unknown ]` |

---

## 4. Shopping vs bookable API (ask explicitly)

| Question | Answer |
|---|---|
| Is there a **shopping / fare-cache / Instant Search** API that is cheaper or unlimited? | `[ Yes / No / Unknown ]` |
| Endpoint / product name | `[ ___ ]` |
| Does shopping return bookable offers or indicative only? | `[ bookable / indicative / mixed ]` |
| Must we still call a **pricing/revalidate** API before ticket? | `[ Yes / No ]` |
| Sandbox credentials available by | Date: `________` |

If **Yes** to shopping API: TripOS browse should prefer it once wired (readiness Phase 2+ / Phase E).

---

## 5. Engineering provisional defaults (Farhan — 2026-09-25)

Use until Sahil overrides with contract answers. Safe for **building meters + cache**; not a substitute for real clauses before heavy live traffic.

| Item | Provisional default | Rationale |
|---|---|---|
| What counts as a “look” for our meters | `search` live + `revalidate` live; **not** cache hits; **not** book | Conservative (counts more looks) |
| `L2B_WARN_RATIO` | **80** | Warn before typical mid-market pain |
| `L2B_CRITICAL_RATIO` | **120** | Soft-brake / throttle zone |
| Measurement window | Rolling **7d** for ops; report **30d** for contract reviews | Ops vs commercial |
| Min bookings / month | **Not enforced in software** until Sahil fills §3 | Avoid fake gates |
| Shopping API | Assume **none** until confirmed → Redis shopping cache is our control | Matches readiness Phase 2 |
| Cache TTL default | **120s** hot browse | See readiness Phase 2 |
| First supplier | Mock until sandbox pack filled; prefer first ready of TBO/TripJack | Existing Phase 0 decision |

**Env placeholders (Phase 1+):**

```env
L2B_WARN_RATIO=80
L2B_CRITICAL_RATIO=120
SEARCH_CACHE_ENABLED=false
SEARCH_CACHE_TTL_SECONDS=120
```

---

## 6. Sahil / Nilesh shortcut

Reply once with either:

1. **“Accept Farhan L2B provisional defaults”** + supplier name when known, **or**  
2. This file filled (or answers in chat) + date.

Until then TripOS may implement Phases 1–2 of `live-inventory-readiness-plan.md` against provisional defaults. **Do not** run high-volume live production search until §2–§4 are filled or explicitly waived.

---

## 7. Sign-off

| Role | Name | Date | Ack |
|---|---|---|---|
| Engineering (provisional defaults locked) | Farhan | 2026-09-25 | Phase 0 engineering closed |
| Supplier pack / contract truth | Sahil | | |
| Commercial awareness | Nilesh | | |
