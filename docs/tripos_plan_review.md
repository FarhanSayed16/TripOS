# TripOS — Comprehensive Plan Review & Issues Report

### Deep analysis of all 10 planning documents for gaps, inconsistencies, and missing pieces

**Status: APPLIED (2026-09-16)** — All critical/important/minor fixes and enhancements A–E were folded into:
- `tripos-implementation-plan.md` §0.1 (locked decisions)
- `tripos-master-plan.md` (phase checklists)
- `tripos-modules-and-flow.md`
- `tripos-backend-plan.md` / `tripos-frontend-plan.md` / `tripos-enhancements.md` / `tripos-docs-index.md`

Keep this file as an audit trail. **Do not treat open issues below as still open** unless marked deferred.

---

**Documents reviewed:**
- [tripos-plan.md](file:///d:/TripOS/docs/tripos-plan.md) — Vision & business
- [tripos-implementation-plan.md](file:///d:/TripOS/docs/tripos-implementation-plan.md) — Architecture & phased delivery
- [tripos-frontend-plan.md](file:///d:/TripOS/docs/tripos-frontend-plan.md) — UI pages, design, navigation
- [tripos-backend-plan.md](file:///d:/TripOS/docs/tripos-backend-plan.md) — Modules, services, build order
- [tripos-master-plan.md](file:///d:/TripOS/docs/tripos-master-plan.md) — 40-phase execution checklist
- [tripos-modules-and-flow.md](file:///d:/TripOS/docs/tripos-modules-and-flow.md) — Module breakdown & flows
- [tripos-enhancements.md](file:///d:/TripOS/docs/tripos-enhancements.md) — Ideas backlog
- [tripos-ai-spec.md](file:///d:/TripOS/docs/tripos-ai-spec.md) — AI Copilot contract
- [tripos-work-division.md](file:///d:/TripOS/docs/tripos-work-division.md) — Ownership
- [tripos-docs-index.md](file:///d:/TripOS/docs/tripos-docs-index.md) — Document map

---

## Overall Verdict

> [!IMPORTANT]
> The planning documentation is **exceptionally thorough and well-structured** — among the best startup planning doc sets I've seen. The architecture is sound, the phasing is disciplined, and the "what NOT to build" boundaries are clear. However, there are **18 issues** ranging from contradictions between documents to missing operational details that should be resolved before Phase 0 exits. None are fatal, but several will cause confusion or rework during build.

---

## Issue Severity Legend

| Severity | Meaning |
|---|---|
| 🔴 **Critical** | Will cause build confusion, data bugs, or money errors if not resolved before coding |
| 🟡 **Important** | Inconsistency between docs or missing detail that will block a phase |
| 🟢 **Minor** | Polish, clarity, or future-proofing suggestion |

---

# 🔴 CRITICAL ISSUES (5)

---

### Issue 1: WhatsApp Module Contradiction — wa.me vs Cloud API in V1

**Location:** [tripos-modules-and-flow.md L160-174](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L160-L174) vs every other document

**Problem:** `tripos-modules-and-flow.md` §2.8 says:

> *"Use WhatsApp Business Cloud API or a provider (Interakt/AiSensy) — don't build raw integration."*

This **directly contradicts** every other document which explicitly locks V1 to **wa.me deep links only** (no Cloud API):

- [tripos-plan.md L108](file:///d:/TripOS/docs/tripos-plan.md#L108): `WhatsApp (V1): wa.me deep links`
- [tripos-implementation-plan.md L226](file:///d:/TripOS/docs/tripos-implementation-plan.md#L226): `wa.me links`
- [tripos-master-plan.md L31](file:///d:/TripOS/docs/tripos-master-plan.md#L31): `V1 WhatsApp = wa.me (not Cloud API)`
- [tripos-docs-index.md L50](file:///d:/TripOS/docs/tripos-docs-index.md#L50): `WhatsApp V1: wa.me links`
- [tripos-backend-plan.md L252-256](file:///d:/TripOS/docs/tripos-backend-plan.md#L252-L256): `wa.me link service` with Cloud API later

**Impact:** If someone reads `modules-and-flow.md` first (which is in the recommended reading), they'll scope the Messaging module for Cloud API integration — wasting weeks on Meta template approvals, webhook setup, and BSP selection that aren't needed in V1.

**Fix:** Update `tripos-modules-and-flow.md` §2.8 to match. Replace the Cloud API mention with:

> *"V1: Generate wa.me deep links (agent opens WhatsApp with prefilled text). No server-side send, no Meta Cloud API, no template approvals. Build the module with a provider interface so V2/V3 can swap to Cloud API without changing Quote/Payment modules."*

---

### Issue 2: Missing Passenger Data Timing Decision

**Location:** [tripos-enhancements.md L49-55](file:///d:/TripOS/docs/tripos-enhancements.md#L49-L55) flags this, but NO other doc resolves it

**Problem:** The enhancements doc correctly identifies that passenger details (names, DOB, passport) are required by supplier APIs for booking, but **no planning document locks the decision** on WHEN these are collected:

- **Option A:** Before payment (agent fills pax → generates pay link)
- **Option B:** After payment, before supplier confirm (payment webhook → `pending_pax` state → agent fills → confirm)
- **Option C:** Customer fills pax on the public quote page before paying

The master plan Phase 14 says "Attach passengers/guests (flights require pax before send/pay — enforce rule)" — but this is **buried in one sub-bullet** and contradicts the status machine `draft → ready → sent → paid` which has no `pending_pax` state.

**Impact:** This affects:
- Database schema (Phase 4) — where `quote_passengers` lives
- Quote status machine — needs a `pax_required` gate
- Public quote page — does the customer enter pax or only the agent?
- Booking confirm job — what happens if pax data is missing when webhook fires?
- The entire UX flow for the agent

**Fix:** Add an explicit decision section to `tripos-implementation-plan.md` or the master plan. Recommended: **Collect pax BEFORE payment link creation** (Option A) for flights. This is the safest path — you never have "paid but can't book because no names."

---

### Issue 3: Commission Calculation Formula is Undefined

**Location:** [tripos-modules-and-flow.md L386-399](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L386-L399), [tripos-enhancements.md L178](file:///d:/TripOS/docs/tripos-enhancements.md#L178)

**Problem:** Flow E says:
> `supplier payout − customer price = agent commission`

This formula is **backwards** — supplier payout is always *less* than customer price (agent marks UP from cost). The correct formula is:
> `customer_price − supplier_cost = total_margin`
> Then: `total_margin = platform_fee + agent_commission`

No document defines:
- What percentage goes to the platform vs the agent
- Whether the platform takes a flat fee, percentage, or per-booking fee
- Whether this varies by product type (flight vs hotel)
- How the platform fee interacts with the agent's own markup

The enhancements doc mentions "Distinguish platform fee vs agent markup vs supplier payout" but this is tagged V2 — yet the database schema includes `commissions` table references in V1.

**Impact:** The `quote_items` table needs `supplier_cost`, `agent_markup`, `platform_fee`, and `customer_total` columns. If the schema is wrong, V2 commissions become a painful migration.

**Fix:** Even though commission *logic* is V2, the **data model** must be correct in V1:
1. Fix the formula in `tripos-modules-and-flow.md`
2. Add a commercial decision item to Phase 0: "What is the platform's cut per booking?"
3. Ensure `quote_items` schema stores all four amounts from day one

---

### Issue 4: No Error/Timeout Handling for Revalidation Failures at Payment Time

**Location:** Gap across [tripos-implementation-plan.md L366-376](file:///d:/TripOS/docs/tripos-implementation-plan.md#L366-L376) and [tripos-master-plan.md L675-691](file:///d:/TripOS/docs/tripos-master-plan.md#L675-L691)

**Problem:** The happy path flow shows:
> `Customer pays → Webhook → revalidate again → book`

But what happens when revalidation fails AFTER payment is captured? The docs say:
> "Pay captured BUT book fails → booking = needs_manual_support / failed → notify agent + admin → do NOT auto-refund"

However, this conflates two very different failures:
1. **Fare changed** (price went up ₹2,000) — Is this a full refund case or can the agent approve the difference?
2. **Offer expired / sold out** — Must refund, no alternative
3. **Supplier API timeout** — Should retry, not immediately fail
4. **Supplier returned an unknown error** — Needs investigation

Each needs a different status and different agent/admin action. The current plan lumps them all into `needs_manual_support`.

**Impact:** In pilot, "payment taken but booking failed" will be the #1 support fire. Without clear sub-statuses, you'll be manually reading logs for every case.

**Fix:** Define booking failure sub-reasons in the status machine:
```
booking_failed_fare_changed
booking_failed_sold_out  
booking_failed_supplier_timeout (retryable)
booking_failed_supplier_error
booking_failed_unknown
```
Add these to Phase 23 (Audit log & failure states) and the schema in Phase 4.

---

### Issue 5: No CORS / Cookie Strategy for Cross-Domain Auth (Vercel → Render)

**Location:** Gap in [tripos-backend-plan.md](file:///d:/TripOS/docs/tripos-backend-plan.md) and [tripos-frontend-plan.md](file:///d:/TripOS/docs/tripos-frontend-plan.md)

**Problem:** The stack locks frontend on **Vercel** (e.g. `app.tripos.in`) and backend on **Render** (e.g. `api.tripos.in`). These are different domains. The auth plan says:

> "JWT access + refresh (HttpOnly cookies preferred)"

**HttpOnly cookies don't work cross-domain by default.** With `SameSite=Lax` (browser default), cookies set by `api.tripos.in` won't be sent from `app.tripos.in`. You'd need:
- Same parent domain with `SameSite=None; Secure` — requires HTTPS + explicit config
- OR a BFF (Backend-for-Frontend) proxy on the Next.js side to forward API calls as same-origin
- OR switch to `Authorization: Bearer` header tokens stored in memory (not localStorage) with a cookie-based refresh token on a same-domain path

None of this is addressed in any planning doc.

**Impact:** Auth will silently fail on first deploy if this isn't designed. This is Phase 3/5 work.

**Fix:** Add a section to `tripos-backend-plan.md` §11 (Cross-cutting checklist) or Phase 3/5 of the master plan:
- Decision: BFF proxy on Next.js OR `Authorization` header with HttpOnly refresh cookie
- If cookie auth: document domain strategy (`*.tripos.in` parent domain for both services)
- CORS config must allowlist exact Vercel preview URLs during development

---

# 🟡 IMPORTANT ISSUES (8)

---

### Issue 6: Build Order Conflict — Modules-and-Flow vs Master Plan

**Location:** [tripos-modules-and-flow.md L437-449](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L437-L449) vs [tripos-master-plan.md L44-88](file:///d:/TripOS/docs/tripos-master-plan.md#L44-L88)

**Problem:** The modules doc says:
> Week 3–4: Search (flight + hotel, one supplier)
> Week 5–6: Quotation Engine, Customer CRM

The master plan says:
> Phase 10 (roughly week 3): CRM customers
> Phase 11-12 (roughly week 3-4): Adapter platform + Inventory search
> Phase 13: Search frontend
> Phase 14-15: Quotes engine + UI

CRM comes **before** Search in the master plan but **after** in the modules doc. Since quotes need a customer attached, the master plan's order (CRM first) is correct.

**Fix:** Update `tripos-modules-and-flow.md` §5 build order to match the master plan sequence.

---

### Issue 7: Missing `organization_members` Mention in Modules-and-Flow

**Location:** [tripos-modules-and-flow.md L43](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L43)

**Problem:** The Auth module says it owns `organizations`, `users`, `sessions` — but doesn't mention `organization_members` (the join table for user↔org with roles). The backend plan, implementation plan, and master plan all include this table. Since multi-member orgs and role checks (`agent` vs `admin`) are V1, this is a real omission.

**Fix:** Update §2.1 data owned to: `organizations, users, organization_members, sessions`

---

### Issue 8: Inconsistent Login Method — Email+Password vs Phone+OTP

**Location:** [tripos-modules-and-flow.md L39](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L39) vs [tripos-backend-plan.md L113](file:///d:/TripOS/docs/tripos-backend-plan.md#L113)

**Problem:**
- Modules-and-flow says: *"Login (email/phone + password **or OTP**)"*
- Backend plan says: *"Login issues access + refresh"* with *"Password hashing (argon2)"* — no OTP mention
- Implementation plan says: *"argon2 passwords; email verification via Resend"*

OTP login is a **significantly different build** (needs SMS provider, phone verification, rate-limited OTP generation). If V1 is email+password only, the modules doc is misleading.

**Fix:** Clarify that V1 is email + password only. OTP/phone login is V1.5 or V2 if pilot agents demand it.

---

### Issue 9: `tripos-modules-and-flow.md` References Deleted/Renamed Document

**Location:** [tripos-modules-and-flow.md L3](file:///d:/TripOS/docs/tripos-modules-and-flow.md#L3)

**Problem:** The header says "Companion to the master plan (`tripos-plan.md`)" — but `tripos-plan.md` is the *vision* doc, not the master plan. The actual master plan is `tripos-master-plan.md`. This doc was written before the master plan existed.

**Fix:** Update the companion reference to include `tripos-master-plan.md` and clarify the doc's role in the reading order.

---

### Issue 10: No Rate Limiting Strategy Defined for V1

**Location:** Gap across backend plan and implementation plan

**Problem:** Multiple docs mention rate limiting:
- [tripos-implementation-plan.md L454](file:///d:/TripOS/docs/tripos-implementation-plan.md#L454): "Per org + per supplier"
- [tripos-backend-plan.md L499](file:///d:/TripOS/docs/tripos-backend-plan.md#L499): "Inventory + optional Redis"
- [tripos-enhancements.md L170](file:///d:/TripOS/docs/tripos-enhancements.md#L170): "Rate-limit + search abuse protection per agent"

But no doc defines:
- What the actual limits should be (searches per minute per org? per user?)
- Whether rate limits are Redis-required (Upstash) or can use in-memory for pilot
- Whether supplier rate limits (TBO/TripJack impose their own) are tracked server-side

**Impact:** Suppliers will throttle or block you if an agent hammers search. This is especially dangerous during pilot when you're proving reliability.

**Fix:** Add to Phase 12 (Inventory search) in the master plan:
- Default rate limit: e.g., 30 searches/min per org
- In-memory `TokenBucket` for pilot; migrate to Redis when Upstash is added
- Log supplier rate limit headers and respect `Retry-After`

---

### Issue 11: No Data Backup/Recovery Plan for V1 Pilot

**Location:** Not mentioned until [tripos-master-plan.md Phase 39](file:///d:/TripOS/docs/tripos-master-plan.md#L1096-L1117) (Scale phase)

**Problem:** Backup/restore is mentioned only in Phase 39 (V3 scale). But you're handling **real money and real bookings** from Phase 29 (pilot). If Render Postgres has an issue or a bad migration corrupts data during pilot, you need recovery.

**Fix:** Add to Phase 27 (Production deploy) or Phase 28 (Security gate):
- Confirm Render Postgres automatic backups are enabled
- Document point-in-time recovery process
- Test a restore at least once before pilot

---

### Issue 12: Quote `valid_until` Source Not Defined

**Location:** Referenced in many places but never specified how the value is determined

**Problem:** Quotes have `valid_until` and are expired by a background job. But:
- Who sets the value — the agent manually, or the system automatically?
- Is it based on supplier fare hold time (if the supplier supports holds)?
- What's the default? 2 hours? 6 hours? End of day?
- Can the agent override it?

**Impact:** If defaults are wrong, agents either have quotes expire too fast (frustrating) or too slow (fare changes cause booking failures).

**Fix:** Add to Phase 14 (Quotes engine):
- Default `valid_until`: 4 hours from quote creation (configurable per org later)
- Agent can extend up to 24 hours (but system warns about fare risk)
- Revalidation is still mandatory before payment regardless of expiry

---

### Issue 13: No Logging/Monitoring Plan for V1 Pilot

**Location:** [tripos-implementation-plan.md L229](file:///d:/TripOS/docs/tripos-implementation-plan.md#L229) mentions "Structured logs (JSON) + Sentry + OpenTelemetry later" but no detail

**Problem:** The plan says Sentry + structured logs, but:
- No mention of where logs are stored/viewed on Render (Render has basic log streaming but no retention)
- No log retention strategy for pilot support
- No alerting for critical events (payment webhook failures, booking confirm failures)
- Sentry is listed but not in Phase 27 (deploy) checklist

**Impact:** During pilot, when a booking fails at 11pm, you need to diagnose it quickly. Without proper logging and alerts, you'll be guessing.

**Fix:** Add to Phase 27/28:
- Sentry DSN configured for API + worker
- Sentry alerts on: unhandled exceptions, booking confirm failures, payment webhook signature failures
- Consider Render log drain to a free tier of Papertrail/Betterstack for searchable logs during pilot

---

# 🟢 MINOR ISSUES (5)

---

### Issue 14: Enhancements Doc References Non-Existent `tripos-execution-plan.md`

**Location:** [tripos-enhancements.md L327](file:///d:/TripOS/docs/tripos-enhancements.md#L327)

**Problem:** The enhancements doc says the next step is to produce `tripos-execution-plan.md`. This was never created — the `tripos-master-plan.md` effectively replaces it. The reference is stale.

**Fix:** Update to reference `tripos-master-plan.md` as the execution doc.

---

### Issue 15: Backend Plan References Non-Existent `tripos-ai-spec.md` as `tripos-sahil-ai-handoff.md`

**Location:** [tripos-backend-plan.md L593](file:///d:/TripOS/docs/tripos-backend-plan.md#L593)

**Problem:** The backend plan's document map references `tripos-ai-spec.md` correctly, but the AI spec itself mentions it was "formerly `tripos-sahil-ai-handoff.md`". The backend plan also doesn't list the master plan or docs index in its document map (written before those existed).

**Fix:** Update backend plan document map to include `tripos-master-plan.md` and `tripos-docs-index.md`.

---

### Issue 16: Frontend Plan Lists 5 Surfaces But Table Shows 4

**Location:** [tripos-frontend-plan.md L15-24](file:///d:/TripOS/docs/tripos-frontend-plan.md#L15-L24)

**Problem:** The text says "Plan **four surfaces**" but the table lists **five** (A through E: Marketing, Auth, Agent OS, Admin OS, Public customer). This is a cosmetic error — the content is correct with 5 surfaces.

**Fix:** Change "four surfaces" to "five surfaces".

---

### Issue 17: Master Plan Phase 0.1 Has Checked Items But Phase 0 Not Done

**Location:** [tripos-master-plan.md L101-104](file:///d:/TripOS/docs/tripos-master-plan.md#L101-L104)

**Problem:** Phase 0.1 has `[x]` on role confirmations, but Phase 0.4 (exit gate) items are all `[ ]`. The change log says the master plan was created on 2026-09-16, so checking items before the team has reviewed feels premature.

**Fix:** Either leave all unchecked until team review, or add a note that 0.1 was pre-confirmed via prior discussions.

---

### Issue 18: Inconsistent Module Naming — "Agent Management" vs "Admin Module"

**Location:** [tripos-modules-and-flow.md](file:///d:/TripOS/docs/tripos-modules-and-flow.md) §2.2 calls it "Agent Management (Admin)" while [tripos-backend-plan.md](file:///d:/TripOS/docs/tripos-backend-plan.md) §5.9 calls it "Admin module"

**Problem:** The same module has different names across documents. The backend plan's `modules/admin/` is the canonical folder name.

**Fix:** Standardize on "Admin module" everywhere, since that's what the code folder will be called.

---

# ENHANCEMENTS TO ADD TO THE PLAN

These are not bugs in the existing docs but **missing items** that should be addressed before or during V1 build.

---

### Enhancement A: Add Health Check to Frontend

**Why:** The master plan has `/health` and `/ready` for the backend (Phase 3) but nothing for the frontend. Vercel has deployment checks, but you should have a `/api/health` BFF route that verifies the frontend can reach the backend API. This catches misconfigured `NEXT_PUBLIC_API_URL` on deploy.

**Where:** Add to Phase 8 or 27.

---

### Enhancement B: Define Webhook Retry Window

**Why:** Razorpay retries webhooks for up to 24 hours. The backend needs to handle out-of-order and delayed webhooks. The current plan says "idempotent" but doesn't specify:
- What if the webhook arrives for an already-expired quote?
- What if a webhook arrives minutes after a manual "mark as failed"?

**Where:** Add to Phase 18/26.

---

### Enhancement C: Add Customer Phone Format Validation

**Why:** The CRM stores customer phone for WhatsApp wa.me links. wa.me requires international format (e.g., `919876543210`). Indian agents will enter `09876543210` or `+91-98765-43210`. Without normalization, wa.me links will break silently.

**Where:** Add phone normalization to Phase 10 (CRM) and Phase 16 (Messaging wa.me).

---

### Enhancement D: Define Quote Token Security

**Why:** Public quote pages use `/q/[token]`. If tokens are sequential IDs or guessable, anyone can view any quote. Tokens should be:
- Cryptographically random (e.g., UUID v4 or a signed short token)
- Not containing the quote ID or org ID
- Optionally time-limited (though the quote itself has expiry)

**Where:** Add to Phase 14 (Quotes engine) and Phase 17 (Public quote).

---

### Enhancement E: Add Search Result Pagination/Limits

**Why:** Supplier APIs can return 200+ results for a single flight search. No doc mentions:
- How many results to show the agent
- Whether to paginate or lazy-load
- Whether to pre-sort by price/time
- Server-side vs client-side pagination

**Where:** Add to Phase 12 (backend) and Phase 13 (frontend).

---

## Summary Table

| # | Issue | Severity | Affects Phase |
|---|---|---|---|
| 1 | WhatsApp wa.me vs Cloud API contradiction | 🔴 Critical | 16, 11 |
| 2 | Passenger data timing undecided | 🔴 Critical | 4, 14, 18, 21 |
| 3 | Commission formula wrong + undefined | 🔴 Critical | 4, 33 |
| 4 | No revalidation failure sub-statuses | 🔴 Critical | 4, 21, 23 |
| 5 | No cross-domain auth strategy | 🔴 Critical | 3, 5, 27 |
| 6 | Build order conflict CRM vs Search | 🟡 Important | docs only |
| 7 | Missing `organization_members` in modules doc | 🟡 Important | docs only |
| 8 | Email+password vs phone+OTP inconsistency | 🟡 Important | 5 |
| 9 | Stale document reference in modules doc | 🟡 Important | docs only |
| 10 | No rate limiting specifics | 🟡 Important | 12 |
| 11 | No backup plan for V1 pilot | 🟡 Important | 27, 28 |
| 12 | Quote expiry source undefined | 🟡 Important | 14 |
| 13 | No logging/alerting plan for pilot | 🟡 Important | 27, 28 |
| 14 | Stale reference to non-existent execution plan | 🟢 Minor | docs only |
| 15 | Incomplete document map in backend plan | 🟢 Minor | docs only |
| 16 | "Four surfaces" should be "five" | 🟢 Minor | docs only |
| 17 | Pre-checked items before team review | 🟢 Minor | docs only |
| 18 | Inconsistent module naming | 🟢 Minor | docs only |

| Enhancement | Where to add |
|---|---|
| A. Frontend health check | Phase 8/27 |
| B. Webhook retry window rules | Phase 18/26 |
| C. Phone format normalization | Phase 10/16 |
| D. Quote token security spec | Phase 14/17 |
| E. Search result pagination | Phase 12/13 |

---

## Recommended Next Step

> [!TIP]
> ~~Resolve the **5 critical issues** before starting Phase 0 exit.~~ **Done — applied to plans.**  
> Proceed with **Phase 0** commercial checklist (especially platform fee rule), then Phase 1 repo scaffolding using `tripos-master-plan.md`.

The overall plan quality is **excellent**. These issues were the kind that only surface when you cross-reference 10 documents — they're now locked so execution stays smooth.
