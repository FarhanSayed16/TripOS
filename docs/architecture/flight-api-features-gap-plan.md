# TripOS × “Top 25 Flight API Features” — Gap Analysis & Implementation Plan

**Purpose:** Map your sir’s OTA Flight API checklist against **what TripOS actually has today**, add **global currency** + **multilingual**, recommend a few TripOS-specific extras, and give a **phase-wise plan** to close the gaps.

**Date:** 2026-09-28  
**Audience:** Farhan (build) · Nilesh (commercial / supplier) · Sahil (supplier contract / API access)  
**Related:**  
- **Execution plan (build this next)** → [`flight-commerce-implementation-plan.md`](./flight-commerce-implementation-plan.md) ← **phase-wise FC 0–8**  
- Live inventory readiness (L2B Phases 0–7) → [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md)  
- Conceptual L2B story → [`live-inventory-phases-0-7-explained.md`](./live-inventory-phases-0-7-explained.md)  
- Inventory honesty → [`inventory-v1-mock.md`](./inventory-v1-mock.md)

---

## 0. Important framing (read this first)

The infographic describes an **ideal Flight API for an OTA**. TripOS is slightly different:

| Infographic assumes | TripOS actually is |
|---|---|
| You *are* (or buy) a rich flight distribution API | You are a **B2B agent operating system** that *consumes* supplier APIs (TBO / TripJack / later GDS·NDC·LCC) |
| Features live “inside the Flight API” | Features split across **supplier capability** + **TripOS product layer** |

So every feature falls into one of three buckets:

| Bucket | Meaning | Who unblocks it |
|---|---|---|
| **A — Supplier-dependent** | Content / capability must exist in the supplier feed; TripOS adapts + normalizes | Nilesh / Sahil + adapter work |
| **B — TripOS product** | We build UX, orchestration, money safety, i18n, currency, ranking, notifications | Farhan (engineering) |
| **C — Commercial / ops** | Contracts, BSP/IATA, credit lines, sandbox keys | Nilesh / Sahil |

**Do we need to implement all 25?**  
Not as a single “become a GDS” project. We **do** need a **phased flight-commerce readiness plan** so that when live suppliers arrive, TripOS can *expose* these capabilities to agents cleanly — and so product gaps (currency, multilingual, ancillaries UX, cancel/refund automation, etc.) are not left forever as “later.”

**Honest baseline today:**  
TripOS has a strong **agent workflow** (search → quote → share → pay → book) and strong **L2B / money-path hardening**. Flight *content* is still **mock / simulated TBO**, not a live multi-source airline API.

---

## 1. Master gap table (25 + your 2 + recommended extras)

### Legend

| Status | Meaning |
|---|---|
| **Present** | Usable in product today (may still be mock-backed) |
| **Partial** | Structure / path exists; incomplete, mock, or ops-manual |
| **Missing** | Not in product |
| **N/A (out of scope V1)** | Not required for TripOS agent OS until commercial asks |

| Priority | Meaning |
|---|---|
| **P0** | Block live supplier / pilot trust |
| **P1** | Needed soon after first live supplier |
| **P2** | Competitive / growth |
| **P3** | Later / only if contract supports |

---

### 1.1 The Top 25 (from the image)

| # | Feature (sir’s list) | Status in TripOS | Bucket | Priority | What exists today | What’s missing / to implement |
|---|---|---|---|---|---|---|
| 1 | **Global airline coverage** | Partial / Mock-only | A | P0 | Search works for any O/D on **mock**; simulated TBO rows | Real domestic + international via live TBO/TripJack (or GDS); carrier catalog honesty |
| 2 | **Real-time flight search** | Partial | A+B | P0 | Search API + agent UI; adapter contract | Live supplier HTTP; truthful availability (not simulated) |
| 3 | **Real-time fare & pricing** | Partial | A+B | P0 | **Revalidate** before pay + before confirm; fare-change UX | Live reprice from supplier; richer mismatch diagnostics |
| 4 | **NDC content** | Missing | A | P2–P3 | — | NDC-capable supplier or aggregator; offer/order models; richer ancillaries |
| 5 | **LCC / Direct Connect** | Missing | A | P1–P2 | Mock “IndiGo-like” names only | Real LCC DC via supplier; separate inventory rules (often non-GDS) |
| 6 | **Booking & ticketing** | Partial | A+B | P0 | Pay → confirm job → PNR on mock/sim | Live book + e-ticket / ticket number; ticket PDF from supplier or vault |
| 7 | **Multiple payment options** | Partial | B+C | P1 | Razorpay Payment Links (card/UPI via Razorpay when live); mock mode | More gateways if needed; **BSP/IATA** is commercial settlement — usually not TripOS V1 |
| 8 | **Ancillary services** | Missing | A+B | P1 | Baggage mentioned as **text** in mock descriptions | Structured seat/baggage/meal APIs; quote line-items; book ancillaries |
| 9 | **Seat map & seat selection** | Missing | A+B | P1 | — | Seat-map fetch + select UI; hold seat with offer/order |
| 10 | **Fare families** | Missing | A+B | P1 | Flat offer (title + price) | Fare family model (Basic/Flex/…); rules summary; UI comparison |
| 11 | **Promo / private fares** | Missing | A+C | P2 | — | Supplier promo/private fare params; agent-code / deal codes |
| 12 | **Corporate / SME fares** | Missing | A+C | P2 | Orgs are **travel agencies**, not corp negotiated fares | Corporate deal codes / SME products when supplier supports |
| 13 | **Reissue & exchange** | Missing | A+B | P2 | Docs say V2 / manual | Change-date / reissue flow; fare difference collect; supplier change API |
| 14 | **Cancellation & refund API** | Partial | A+B | P1 | Quote cancel → adapter.cancel (mock); **manual** Razorpay refund runbooks; Refund table | Automated cancel + refund status; policy-driven refunds; customer-facing status |
| 15 | **Fare rules & conditions** | Missing | A+B | P1 | — | Fare-rules endpoint; display change/cancel penalties on quote |
| 16 | **Multi-source aggregation** | Partial | B | P1 | Multi-supplier strategy (all / primary / failover); concatenates offers | Live 2nd supplier (TripJack); **dedupe / merge**; source badges |
| 17 | **Smart offer / result ranking** | Missing | B | P2 | Adapter order; optional AI draft pick (not ranking) | Sort/rank by price, duration, stops, value score; filters |
| 18 | **High API performance** | Partial | B | P0 | Redis shopping cache, singleflight, warm refresh, L2B brakes (feature-flagged) | Enable in staging/prod with live suppliers; SLA monitoring |
| 19 | **API security & authentication** | Present | B | — | JWT + refresh rotation, argon2, CORS, webhook HMAC, org isolation | Continuously harden; partner API keys if public API later |
| 20 | **API monitoring & analytics** | Partial | B | P1 | structlog, Sentry optional, admin analytics, L2B dashboards, dead-letters | Latency/error SLOs per supplier; booking funnel metrics; alerting playbooks |
| 21 | **Booking status & notifications** | Partial | B | P1 | Booking statuses in UI/DB; wa.me share; email for auth | Supplier status poll API; push (WhatsApp Cloud / email) on confirm/fail/refund |
| 22 | **Interline / codeshare** | Missing | A | P2–P3 | Free-text segments only | Structured segments + operating vs marketing carrier |
| 23 | **AI & personalization** | Partial | B | P2 | Opt-in AI copilot (parse + search-draft); L2B-guarded | Preference memory; ranked suggestions; keep cache-only under L2B critical |
| 24 | **Scalability & reliability** | Partial | B | P0 | Outbox worker, circuit breaker, rate limits, L2B survival | Proven under live load; multi-instance Redis rate limits if needed |
| 25 | **Developer docs & sandbox** | Partial | B+C | P1 | Strong **internal** docs + FastAPI `/docs`; mock pilot | Partner sandbox guide; Postman; supplier sandbox keys filled; public API docs if exposed |

---

### 1.2 Your two added features

| # | Feature | Status | Bucket | Priority | What to implement |
|---|---|---|---|---|---|
| 26 | **Global currency converter** | Missing | B (+A) | P1 | Display + quote currency conversion (FX rates with source + timestamp); settle/pay currency policy (start: display convert, charge still INR until multi-currency payments); supplier amount ↔ display amount; admin FX provider config |
| 27 | **Multilingual (i18n)** | Missing | B | P1 | Locale per org/user; UI strings (EN + HI first); API error messages localized; WhatsApp/quote templates localized; AI locale-aware; keep money/dates format locale-safe |

---

### 1.3 Recommended extras (TripOS-specific — beyond the image)

These are **not** on the poster but matter more for a **B2B agent OS** than some GDS niceties:

| # | Feature | Status | Priority | Why add it |
|---|---|---|---|---|
| 28 | **Agent markup & quote honesty** | Present / Partial | P0 keep | Core TripOS value — continue improving transparency (indicative cache badge, fare-change modal) |
| 29 | **L2B / shopping cache control plane** | Present (flagged) | P0 | Already built Phases 0–7 — enable with live suppliers |
| 30 | **White-label branding** | Partial | P1 | Agency-facing product differentiator |
| 31 | **Commission / wallet ledger** | Partial | P1 | B2B monetization — settle + statements |
| 32 | **Document vault (tickets/vouchers)** | Partial | P0 | Durable tickets (R2/S3) — finish staging smoke |
| 33 | **Hotel inventory parity** | Partial / Mock | P1 | Same adapter path; don’t let hotels lag flights badly |
| 34 | **Offer snapshot immutability** | Present | — | Quotes freeze offers — keep this sacred when ancillaries/NDC arrive |
| 35 | **Idempotent pay / book** | Partial | P0 | Prevent double-charge / double-PNR under retries |
| 36 | **Supplier health dashboard** | Partial | P1 | Per-supplier latency, error %, circuit state, L2B contribution |
| 37 | **SSR / special requests** | Missing | P2 | Wheelchair, meal codes — often needed for real bookings |
| 38 | **Schedule change / disruption handling** | Missing | P2 | Notify agent when airline changes schedule |
| 39 | **Audit trail for compliance** | Partial | P1 | Who searched / quoted / paid / booked — strengthen export |
| 40 | **Partner / public API (optional)** | Missing | P3 | If TripOS becomes “API for agencies,” need keys, sandbox, rate limits — only after internal product is solid |

---

## 2. Summary scorecard

| Group | Present | Partial | Missing |
|---|---|---|---|
| Sir’s Top 25 | ~1 (security) | ~12 | ~12 |
| Your adds (currency + i18n) | 0 | 0 | 2 |
| Recommended extras | ~3 | ~7 | ~3 |

**Bottom line for your sir:**  
TripOS is **strong on agent OS + payment safety + L2B**, and **weak on rich airline content features** (NDC, ancillaries, fare families, reissue, multi-currency, multilingual). Closing the gap is **real work**, but it must be sequenced: **live inventory first**, then **content richness**, then **service automation**, with **currency + multilingual** as parallel product tracks.

---

## 3. What should we actually implement? (decision filter)

Implement a feature in TripOS only if **at least one** is true:

1. **We can deliver value without waiting for NDC/GDS** (currency display, i18n, ranking, notifications, docs, analytics).  
2. **First live supplier (TBO/TripJack) exposes it** (search, book, cancel, fare rules, some ancillaries).  
3. **It protects money / L2B / trust** (revalidate, cache, refunds visibility, vault).  
4. **Commercial commits to the contract** (private fares, corporate, BSP).

**Do not** build full NDC order models or BSP settlement in the first wave unless Sahil confirms the feed supports them.

---

## 4. Phase-wise implementation plan

> **Superseded for day-to-day build:** use **[`flight-commerce-implementation-plan.md`](./flight-commerce-implementation-plan.md)** (FC Phases 0–8 with surfaces + acceptance).  
> Waves below are kept as a short summary only.

Naming historically: **Flight Commerce Waves (FC)** — now formalized as **FC Phases 0–8**.

```text
Prerequisite: L2B Phases 0–7 DONE (measure, cache, fare-change, org brakes, refresh, vault, survival)
               + Sahil sandbox keys + contract L2B truth before heavy live search
```

---

### Wave 0 — Truth & foundation (1–2 weeks) — **P0**

**Goal:** Stop lying to ourselves about inventory; lock commercial gates.

| Work | Owner | Outcome |
|---|---|---|
| Fill supplier sandbox pack + L2B contract truth | Sahil | Real warn/critical ratios |
| Choose first live supplier (TBO **or** TripJack) | Nilesh | One primary feed |
| Real HTTP adapter (replace simulated TBO) | Farhan | Live search / revalidate / book in staging |
| Enable Redis shopping cache + vault creds in staging | Farhan | L2B + durable docs |
| Hosted smoke (search → quote → pay → book) | Farhan | Proof on staging |

**Exit:** Staging booking with **real** supplier sandbox PNR (or documented sandbox limitation).

---

### Wave 1 — Core flight commerce parity (2–4 weeks) — **P0/P1**

**Goal:** Match poster items that every serious flight product needs day-one.

| # | Feature | Scope |
|---|---|---|
| 1–3, 6 | Live search, reprice, book/ticket | Adapter + ticket number / document into vault |
| 15 | Fare rules | Fetch + show on quote (even if PDF/text from supplier) |
| 14 | Cancel + refund path | Supplier cancel API + refund status in admin (auto where Razorpay allows; else guided) |
| 16 | Aggregation v1 | Second supplier **or** solid primary + failover; source label on offers |
| 18, 24 | Performance / reliability | Cache on; circuit breaker tuned; supplier error dashboards |
| 20 | Monitoring | Per-supplier latency + book success % |
| 35 | Idempotency audit | Pay/book retry safety review |

**Exit:** Agent can search live, see rules, book, cancel, and ops can see refund state without only using Slack.

---

### Wave 2 — Currency + Multilingual (2–3 weeks, parallelizable) — **P1**  ★ your asks

**Goal:** Global-ready product surface for agencies and travelers.

#### 2A — Global currency

| Step | Detail |
|---|---|
| FX service | Pluggable rate provider (manual admin table first, then API) with `as_of` timestamp |
| Display conversion | Search/quote UI shows amount in org/user preferred currency |
| Snapshot honesty | Quote stores **supplier currency + amount** and **display currency + rate used** |
| Payment policy v1 | Keep charging in **INR** (or supplier settle currency) until multi-currency Razorpay is approved — convert for **display** first |
| Rounding rules | Document banker’s vs commercial rounding; never invent fares |

#### 2B — Multilingual

| Step | Detail |
|---|---|
| Locale model | `org.default_locale`, `user.locale` (start `en`, `hi`) |
| UI i18n | Next.js message catalogs for agent + public quote pages |
| API messages | Map `AppError` codes → localized strings |
| Templates | Quote WhatsApp text + email localized |
| AI | Pass locale into copilot prompts / responses |
| Numbers/dates | `Intl` formatting per locale; currency symbol from Wave 2A |

**Exit:** Agency can set Hindi; public quote page + errors render in that locale; amounts show converted currency with rate timestamp.

---

### Wave 3 — Rich offers (ancillaries & fare families) (3–5 weeks) — **P1**

**Depends on:** supplier supporting ancillaries / branded fares.

| # | Feature | Scope |
|---|---|---|
| 10 | Fare families | Normalize branded fares; compare UI on search |
| 8–9 | Ancillaries + seat map | Select seat/baggage/meal → add to quote total → revalidate → book |
| 17 | Smart ranking | Price / duration / stops / “best value”; filters |
| 21 | Notifications v1 | Email + (optional) WhatsApp Cloud on booking confirmed / failed |

**Exit:** Agent can sell Flex vs Basic and add a seat without leaving TripOS.

---

### Wave 4 — Servicing & growth (3–6 weeks) — **P2**

| # | Feature | Scope |
|---|---|---|
| 13 | Reissue / exchange | Change request → supplier quote difference → collect → confirm |
| 11–12 | Promo / corporate fares | Deal codes from org settings when contract allows |
| 4–5 | NDC / LCC | Only if supplier/aggregator provides; extend offer model |
| 22 | Codeshare / interline | Structured segments |
| 23 | AI personalization | Preferences + ranked suggestions (still L2B-safe) |
| 7 | Payments expansion | Extra methods only if commercial needs beyond Razorpay |
| 30–31 | White-label + commissions polish | Production DNS + settle statements |
| 38 | Schedule change | Ingest supplier notifications when available |

**Exit:** Post-booking changes are productized; content sources expand without rewriting the OS.

---

### Wave 5 — Platform / partner API (optional) — **P3**

Only if TripOS will sell “API access” to other OTAs/agents:

- Public API keys, sandbox tenant, OpenAPI partner portal  
- Stricter rate limits + L2B quotas per partner  
- Webhooks for booking status  

**Exit:** External integrator can complete sandbox book using docs alone.

---

## 5. Suggested calendar (realistic)

| Week | Focus |
|---|---|
| 0–2 | Wave 0 — live supplier in staging |
| 2–6 | Wave 1 — core commerce + cancel/refund visibility |
| 4–7 | Wave 2 — **currency + multilingual** (overlap with Wave 1) |
| 7–11 | Wave 3 — fare families + ancillaries + ranking |
| 11–16 | Wave 4 — reissue, promo/corp, NDC/LCC if contracted |
| Later | Wave 5 — partner API if strategy says so |

Two-stream option (same idea as L2B plan):

- **Stream A (inventory):** Wave 0 → 1 → 3 → 4 content  
- **Stream B (product):** Wave 2 currency/i18n + notifications + white-label + commissions  

---

## 6. Mapping poster “revenue drivers” → TripOS actions

| Poster says | TripOS action |
|---|---|
| Better inventory | Wave 0–1 live supplier + Wave 4 NDC/LCC |
| Better pricing | Live revalidate + private/promo when contracted |
| Rich NDC / ancillaries | Wave 3–4 |
| Faster search & booking | Shopping cache (done) + ranking (Wave 3) |
| Strong servicing | Cancel/refund + reissue + notifications (Waves 1 & 4) |
| **+ Currency** | Wave 2A |
| **+ Multilingual** | Wave 2B |

**OTA evaluation formula (from poster):**  
`Value = Coverage × Pricing × Content × Conversion × Reliability × Servicing`  

TripOS today is strongest on **Conversion workflow + Reliability scaffolding**, weakest on **Coverage/Content**, and zero on **Currency/Multilingual**. The waves above rebalance that formula without abandoning the agent OS strengths.

---

## 7. Ideal TripOS flight stack (adapted from the poster)

```text
┌─────────────────────────────────────────────────────────────┐
│                     TripOS Agent OS                         │
│  Quotes · Markup · WhatsApp · Pay · Book · Vault · L2B     │
│  Currency display · i18n · Ranking · Notifications          │
└───────────────────────────┬─────────────────────────────────┘
                            │ NormalizedOffer / Order
┌───────────────────────────▼─────────────────────────────────┐
│              Aggregation + strategy + cache                 │
└───────┬──────────┬──────────┬──────────┬────────────────────┘
        │          │          │          │
     Live TBO   TripJack   (later)    (later)
     / GDS       / agg      NDC        LCC DC
```

Poster ideal: `GDS + NDC + LCC + Direct + Aggregation + AI/Ranking + Servicing`  
TripOS path: **one live aggregator/supplier first**, then widen sources; **always** own aggregation, ranking, servicing UX, currency, and i18n in the OS layer.

---

## 8. Explicit non-goals (for early waves)

- Building our own airline switches / GDS  
- Full BSP/IATA settlement inside TripOS V1  
- Perfect NDC before first live TBO/TripJack book works  
- Multi-currency **collection** before Razorpay/commercial approves  
- Translating every admin string on day one (agent + public quote first)

---

## 9. Checklist for “sir review”

**Already in good shape (keep investing):** security, quote→pay→book OS, revalidate, L2B/cache, fare-change UX, basic analytics, document vault path, AI scaffold.

**Must implement next (Waves 0–2):** live supplier, fare rules, cancel/refund visibility, aggregation honesty, **global currency**, **multilingual**, monitoring SLOs.

**Implement when supplier supports (Waves 3–4):** ancillaries, seat map, fare families, reissue, promo/corp, NDC/LCC, codeshare.

**Optional later:** partner public API, BSP, deep personalization.

---

## 10. Next action

1. **Nilesh / Sahil:** confirm first live supplier + capability matrix (**FC Phase 0**).  
2. **Farhan:** execute **[`flight-commerce-implementation-plan.md`](./flight-commerce-implementation-plan.md)** one phase at a time (start Phase 0 → 1).  
3. Do not reopen L2B Phases 0–7 unless survival/cache flags need staging proof.

---

*This document is the product gap plan for Flight API readiness. Execution detail for L2B remains in `live-inventory-readiness-plan.md`. Update statuses here as Waves complete.*
