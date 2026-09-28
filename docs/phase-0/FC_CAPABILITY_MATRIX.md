# FC Phase 0 — Supplier capability matrix

**Purpose:** Lock what the first live supplier can do **before** building FC Phases 6–7 features.  
**Filled by:** Sahil (API capability) · Nilesh (commercial) · Farhan (records engineering defaults)  
**Execution:** `docs/architecture/flight-commerce-implementation-plan.md` Phase 0  
**Status (2026-09-28):** **Template READY** — values PENDING Sahil/Nilesh

Copy filled answers into gitignored `secrets/01-supplier-sandbox.md`.

---

## 1. Primary supplier decision

| Field | Answer |
|---|---|
| **Primary live supplier (pilot)** | `[ TBO / TripJack / Other: ___ ]` |
| **Engineering default until filled** | **TBO** (adapter already in codebase) |
| Environment for pilot | `[ sandbox only / sandbox then prod ]` |
| Sandbox credentials shared by | Date: `________` |
| Products for pilot | `[ flights / hotels / both ]` |

**Nilesh sign-off:** ________ Date: ________  
**Sahil sign-off:** ________ Date: ________

---

## 2. Capability matrix (yes / no / later / unknown)

Mark what the **written API + contract** supports for the primary supplier.

| Capability | FC feature ID | Supported? | Notes / endpoint |
|---|---|---|---|
| Domestic + international search | 1, 2 | `[ ]` | |
| Fare quote / revalidate before ticket | 3 | `[ ]` | |
| Book + PNR | 6 | `[ ]` | |
| E-ticket / ticket number | 6 | `[ ]` | |
| Ticket PDF / itinerary download URL | 6, 32 | `[ ]` | |
| Fare rules / conditions text or structured | 15 | `[ ]` | |
| Cancel booking | 14 | `[ ]` | |
| Refund / void API | 14 | `[ ]` | |
| Booking status poll | 21 | `[ ]` | |
| Fare families / branded fares | 10 | `[ ]` | |
| Seat map | 9 | `[ ]` | |
| Ancillaries (baggage / meal / seat sell) | 8 | `[ ]` | |
| SSR / special requests | 37 | `[ ]` | |
| Reissue / exchange | 13 | `[ ]` | |
| Promo / private fares | 11 | `[ ]` | |
| Corporate / SME deal codes | 12 | `[ ]` | |
| NDC content | 4 | `[ ]` | |
| LCC / direct connect distinct feed | 5 | `[ ]` | |
| Codeshare / operating carrier in segments | 22 | `[ ]` | |
| Schedule change notifications | 38 | `[ ]` | |
| Multi-currency supplier amounts | 26 | `[ ]` | |

**Rule:** Anything marked **no / unknown** must stay feature-flagged off in FC Phases 6–7 until this row flips to **yes**.

---

## 3. Product policy locks (Farhan + Nilesh)

| Policy | Locked default (2026-09-28) | Override |
|---|---|---|
| **Charge currency (pay link) V1** | **INR** (display FX = FC Phase 4; multi-currency collection later) | `[ ]` |
| **Locales V1** | **en** + **hi** (FC Phase 5); admin may stay EN-first | `[ ]` |
| **B2B vs B2C** | TripOS = **B2B only**; B2C = separate company via Partner API (FC Phase 8) | Confirmed |
| **Reviews / consumer UGC** | **Out of TripOS scope** (B2C product) | Confirmed |

---

## 4. Staging secrets list (names only — values in password manager)

See full checklist: [`docs/ops/FC_STAGING_SECRETS_CHECKLIST.md`](../ops/FC_STAGING_SECRETS_CHECKLIST.md)

Minimum for FC Phase 1 live spine:

- [ ] `TBO_LIVE_ENABLED=true` (or TripJack equivalent when chosen)
- [ ] Supplier auth env vars (see `.env.example`)
- [ ] `INVENTORY_SUPPLIERS` includes live code (e.g. `tbo` or `tbo` only — drop mock for pure live tests)
- [ ] `SEARCH_CACHE_ENABLED=true` + `REDIS_URL`
- [ ] `DOCUMENT_STORAGE_BACKEND=r2` (or s3) + bucket/keys
- [ ] Razorpay test keys if testing pay→book
- [ ] `SENTRY_DSN` optional but recommended

---

## 5. Exit (Phase 0)

- [ ] Primary supplier name written above  
- [ ] Matrix filled for rows that unblock Phases 2, 6, 7 (at least search/revalidate/book/cancel/fare-rules)  
- [ ] Staging secrets list acknowledged  
- [ ] B2B/B2C + currency + locale policies accepted  

Until Sahil/Nilesh fill: engineering proceeds on **TBO live client scaffold** with simulated fallback (FC Phase 1). Live E2E acceptance stays **blocked on credentials**.
