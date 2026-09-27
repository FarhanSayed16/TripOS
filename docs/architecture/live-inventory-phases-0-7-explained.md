# TripOS — Live Inventory Hardening: What We Built & Why  
### Conceptual walkthrough of Phases 0–7

**Audience:** Product, ops, commercial, and engineering (non-implementation)  
**Date:** 2026-09-25  
**Status:** Engineering for Phases 0–7 complete; Sahil contract truth + hosted smoke still required before heavy live traffic  
**Companion (execution checklist):** [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md)

---

## 1. The problem we set out to solve

TripOS is a B2B agent OS. Today agents can search flights/hotels, build quotes, take payment, and confirm bookings. Until now the pilot could run on **mock** inventory. Turning on **real** suppliers (TBO, TripJack, etc.) changes the economics and risk of the product overnight.

Supplier APIs do not behave like a free Google search. They:

- Count **looks** (live search / pricing calls) against **books** (confirmed bookings)
- Enforce a **Look-to-Book ratio (L2B)** — roughly: how many live calls you make for each confirmed booking
- May **throttle, surcharge, or cut the feed** if L2B is too high or booking volume too low

If every agent browse equals one live supplier call, then:

```text
More agents browsing  →  more live calls  →  worse L2B  →  commercial / feed risk
```

At the same time, travel tech has other “silent killers”: fares moving between browse and pay, payment captured but booking failed, one noisy agency burning the whole platform’s quota, AI explore loops hitting live APIs, and ticket PDFs sitting on ephemeral server disks.

**Phases 0–7** are the coherent answer: measure L2B, cache shopping, protect money paths, brake bad actors, keep cache warm, store documents safely, and auto soft-brake if the platform still goes critical.

---

## 2. One design principle that guides everything

We split traffic into two mental tiers:

| Tier | What the user is doing | Hit live supplier? | Why |
|---|---|---|---|
| **Shopping** | Browsing, comparing, drafting, AI exploring | Prefer **cache** (shared indicative results) | Protect L2B, keep UX fast |
| **Money** | Create pay link, confirm booking | **Always live revalidate** | Price and availability must be real |

TripOS already revalidated before payment and before confirm. What was missing was treating **browse** as shopping — not as a live billable look every time.

Everything below either **reduces unnecessary looks**, **makes remaining looks visible**, or **protects trust and ops when money is involved**.

---

## 3. How the system feels after Phases 0–7

```text
Agent searches a route
        │
        ▼
┌───────────────────────┐
│ Shopping cache (Redis)│── hit ──► Indicative offers (labeled as such)
└───────────┬───────────┘
            │ miss
            ▼
    Live supplier search  (counted as a “look”)
            │
            ▼
     Fill cache for others
            │
            ▼
   Agent builds quote (snapshot)
            │
            ▼
   Revalidate (live) before pay / book
            │
     ┌──────┴──────┐
     │             │
 fare changed    OK → payment → confirm → PNR
     │                    │
  agent accepts        confirmed booking
  new fare             counted for L2B
```

Background: a worker warms popular routes so the next agent often gets a cache hit.  
If platform L2B goes critical: TTL stretches, warm refresh pauses, admins see a banner.

---

## 4. Phase by phase (conceptual)

### Phase 0 — Know the rules before we invent numbers

**What we decided**  
We refuse to “optimize” L2B without knowing what a look is in the supplier contract. Sahil owns supplier truth; engineering locked **provisional** defaults so build could proceed:

- **Warn** around L2B **80**
- **Critical** around L2B **120**
- A **look** = live `search` + live `revalidate` (until contract says otherwise)
- Assume **no** cheaper shopping API until confirmed

**Why**  
Wrong thresholds or wrong look definition = false alarms or silent overspend. Provisional numbers are honest placeholders; Sahil must replace them before heavy production search.

**How it helps**  
The whole platform now shares one vocabulary: warn, critical, looks, books. Later phases plug into those same thresholds instead of inventing their own.

---

### Phase 1 — Measure before you optimize

**What we did (conceptually)**  
Every time TripOS talks to a supplier for search, revalidate, book, or confirmation, we **meter** it — tagged by kind and source (user search vs payment revalidate vs AI vs cache refresh). We roll that into a **7-day L2B** visible in admin.

**Logic**  
You cannot manage what you cannot see. Without meters, “we’re fine on L2B” is a guess. With meters, Nilesh/Farhan/ops can see whether browse traffic is healthy relative to confirmed bookings.

**Why this order**  
Cache and throttles without measurement would hide whether they worked. Phase 1 is the dashboard and the truth source for Phases 2, 4, 5, and 7.

**How it helps**  
- Early warning before the supplier complains  
- Attribution: is the spike user search, AI, or background refresh?  
- Basis for per-org and platform brakes later

---

### Phase 2 — Shopping cache (the main L2B win)

**What we did (conceptually)**  
Identical (or near-identical) route searches within a short time window share one cached result set. Cache hits return **indicative** offers and **do not** count as live looks. Cache misses still go live, then fill the cache for the next agents.

**Logic**  
In B2B travel, many agents search the same popular corridors (DEL–BOM, BOM–GOI, etc.). Paying for that route once per TTL window is enough for shopping. Money moments still revalidate live.

We also use **singleflight**: if ten agents miss the cache at once, only one live call should win the race; the others wait or reuse — not ten parallel billable searches.

**Why Redis / shared cache**  
The cache is route-based, not user-based. One agent’s miss becomes the next agent’s hit. That is how L2B improves with scale instead of collapsing under it.

**How it helps**  
- Dramatically fewer live calls per concurrent agent  
- Faster browse UX  
- Clear product honesty: results can show they came from cache (age / indicative), so agents know revalidate still matters at pay

**Ops note**  
Cache is a feature flag. Mock pilots can leave it off; live suppliers should turn it on with Redis.

---

### Phase 3 — Trust at pay time + money visibility

**What we did (conceptually)**  
Two related money problems:

1. **Fare changed** between quote and pay — the agent must see old vs new amount and choose: accept new fare (refresh) or stay. Silent failure or vague errors destroy trust.
2. **Payment captured / booking failed** — money moved, ticket did not. Ops need a **visible count** of this gap, not only a written SOP.

We also made **quote freshness** configurable (flights shorter TTL, hotels longer) so stale quotes age out before they become surprise fare changes.

**Logic**  
Shopping cache is allowed to be slightly stale. **Payment is not.** Revalidate remains mandatory on the money path; Phase 3 makes the failure mode human and measurable.

**How it helps**  
- Agents can recover from fare change without support theater  
- Ops can prioritize “money stuck” incidents from admin analytics  
- Shorter quote life reduces how often revalidate surprises anyone

---

### Phase 4 — One bad actor cannot sink the feed

**What we did (conceptually)**  
L2B is measured **per organization** as well as platform-wide. After a cache miss, if an org’s ratio is abusive (lots of looks, almost no confirmed books), policy can:

- **Block** further live search (throttle)
- Force **cache-only** browsing
- Or **allow** when healthy

**AI search** is treated as especially dangerous: explore loops can burn looks without booking intent. When org or platform L2B is critical, AI must not open a live-search firehose.

**Logic**  
A platform-wide rate limit (e.g. 30 searches/min) protects TripOS servers. It does **not** protect supplier L2B. One agency doing endless browse-and-abandon can ruin the ratio for everyone. Fairness requires org-level brakes.

**How it helps**  
- Isolates damage to the noisy tenant  
- Gives commercial a fact-based conversation (“your L2B is critical”)  
- Keeps AI as a productivity tool, not a supplier liability

---

### Phase 5 — Keep hot routes warm without waiting for users

**What we did (conceptually)**  
We learn which routes are popular from recent search behavior, then a **background refresher** quietly renews the shopping cache for those routes — with shorter TTL on the hottest band and longer on the warm band.

**Logic**  
Cache only helps if it is **populated**. Depending only on the first unlucky agent of the morning creates a daily spike of live looks. Proactive refresh spreads cost and improves hit rate.

Refresh calls are still metered (as cache refresh), and suppliers with open circuit breakers are skipped — we do not hammer a dying feed.

**How it helps**  
- Agents more often land on cache hits during peak hours  
- Live call rate stays flatter as concurrent agents grow  
- Ops can pause the refresher instantly if L2B spikes (manual kill switch)

---

### Phase 6 — Documents that survive the server

**What we did (conceptually)**  
Tickets, vouchers, and similar files must not live only on the API machine’s local disk. Production hosts are ephemeral: redeploy, restart, or scale-out can wipe local files. We wired a real **object vault** (S3-compatible / Cloudflare R2) for upload and download, and kept the hard rule: **production + local disk = refuse**.

**Logic**  
This is not an L2B feature — it is operational integrity. Live inventory readiness is pointless if confirmed bookings cannot reliably deliver documents.

**How it helps**  
- Tickets survive deploys and multi-instance APIs  
- Share / download flows can use durable storage (including short-lived access links where useful)  
- Staging can smoke-test vault before go-live

---

### Phase 7 — Survival soft-brakes when the platform is already critical

**What we did (conceptually)**  
If **platform** L2B hits critical despite Phases 1–5:

1. **Widen shopping-cache TTL** (e.g. double, hard-capped) so fewer misses → fewer live looks  
2. **Pause warm-band refresh** — keep only the hottest routes refreshed; stop burning looks on nicer-to-have warm routes  
3. **Admin red banner** + **Sentry alert** so humans notice without staring at dashboards  
4. Documented **ops runbook** for confirm / override / clear

**Logic**  
Phases 2–5 are prevention. Phase 7 is **automatic triage**: buy time and cut elective live traffic while conversion and ops catch up. Soft brakes, not a hard kill of the product — agents can still browse (often from longer-lived cache) and money paths still revalidate.

**How it helps**  
- Reduces chance of feed cutoff during a bad week  
- Makes survival mode obvious (banner) instead of silent  
- Gives Farhan/ops a playbook instead of improvising under pressure

---

## 5. How the phases reinforce each other

| Layer | Role |
|---|---|
| Phase 0 | Shared definition of success/failure |
| Phase 1 | Visibility (truth) |
| Phase 2 | Structural L2B reduction (shopping ≠ live) |
| Phase 3 | Money-path honesty + ops visibility |
| Phase 4 | Fairness / isolation of abuse + AI guard |
| Phase 5 | Sustained cache hit rate at scale |
| Phase 6 | Durable proof of booking (documents) |
| Phase 7 | Automatic last-resort soft brakes |

Read it as a stack:

```text
Contract language (0)
    → Measure (1)
        → Cache shopping (2)
            → Warm cache (5)
                → Soft-brake if still critical (7)
        → Brake abusive orgs / AI (4)
        → Fare + pay/book honesty (3)
        → Durable tickets (6)
```

Removing any lower layer weakens the ones above it. Measuring without caching leaves you watching a fire. Caching without org brakes lets one tenant spoil the ratio. Survival without measurement cannot know when to trigger.

---

## 6. What this means for each role

**Agents**  
Faster browse when cache hits; prices labeled indicative when from cache; clear fare-change choice at pay; tickets that do not vanish after a deploy.

**Platform admin / Farhan**  
Rolling L2B, org offenders, survival banner, pause switches, and a written survival runbook.

**Commercial / Nilesh**  
Conversion still matters — soft brakes buy time, they do not replace bookings. Org L2B data supports coaching or limiting bad actors.

**Sahil**  
Must still replace provisional warn/critical and look definitions with contract truth before heavy live search; shopping-API options (if any) remain upside.

---

## 7. What we deliberately did *not* do in these phases

To stay focused, we deferred (among others): multi-item cancel compensation, WhatsApp Cloud API, a separate AI service, auto-settle commissions, full NDC/LCC merge, orphan PNR reconcile, multi-currency.

Those matter later. They were **not** required to make live inventory commercially survivable.

---

## 8. Remaining before “live supplier ready” at scale

Engineering for Phases 0–7 is in place. Still required for a confident GO:

1. **Sahil** — real contract L2B clauses override provisional 80 / 120  
2. **Staging** — Redis + cache on; vault credentials; optional critical-L2B survival simulation  
3. **Hosted smoke + commercial gates** (existing Sprint P / GO V2 checklist)

Until then: pilot carefully, prefer cache on, watch admin L2B, keep survival enabled.

---

## 9. One-paragraph summary

We prepared TripOS for live suppliers by treating **browse as shopping** and **pay/book as money**. We defined L2B rules (Phase 0), measured every look and book (Phase 1), shared route results through a shopping cache (Phase 2), made fare changes and pay/book gaps honest (Phase 3), stopped single orgs and AI from burning the feed (Phase 4), warmed popular routes in the background (Phase 5), put tickets in durable object storage (Phase 6), and auto soft-braked with wider TTL, paused warm refresh, and admin/Sentry alerts when platform L2B still goes critical (Phase 7). Together, that is how TripOS can scale agent search without inviting supplier cutoff — while keeping trust on the money path.

---

*For file-level acceptance and env flags, use [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md). For L2B theory depth, use [`look-to-book-search-cache-plan.md`](./look-to-book-search-cache-plan.md). For survival ops steps, use [`../ops/L2B_SURVIVAL_RUNBOOK.md`](../ops/L2B_SURVIVAL_RUNBOOK.md).*
