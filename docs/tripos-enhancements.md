# TripOS — Enhancements & Ideas Plan

### Companion to `tripos-plan.md`, `tripos-modules-and-flow.md`, and `tripos-work-division.md`

**Purpose of this document:** Capture suggested improvements, flow tweaks, structural refinements, and future ideas *before* locking the execution / work-division plan.  
**Rule:** Nothing here expands V1 unless marked **V1 (small)**. Most items are **deferred by design** so the core loop stays shippable.

**Status:** Proposal — review as a team (Farhan / Sahil / Nilesh), accept / reject / park each item, then fold accepted ones into the execution plan.

---

## 1. How to use this document

| Tag | Meaning |
|---|---|
| **V1 (small)** | Tiny refinement of the existing V1 scope — low cost, high clarity. Safe to include if everyone agrees. |
| **V1.5** | After pilot starts, before full V2 — friction fixes from real agent usage. |
| **V2+** | Builds on a working search → quote → WhatsApp → pay → book loop. |
| **V3+** | Scale, hierarchy, white-label, multi-supplier. |
| **Park** | Good idea, wrong time, or needs commercial/legal clarity from Nilesh first. |

**Decision rule:** Prefer shipping the core loop over any enhancement. If an idea doesn’t increase *Monthly Active Transacting Agents*, park it.

---

## 2. What stays unchanged (do not “enhance away”)

These are deliberate choices in the master plan. Enhancements should wrap around them, not replace them:

1. **B2B agent OS**, not a consumer OTA.
2. **AI never invents price/availability** — only orchestrates real supplier calls.
3. **One FastAPI modular monolith** for V1 — no microservices.
4. **One supplier abstraction layer** — no direct TBO/TripJack calls scattered in the app.
5. **V1 = one org, flat roles (agent / admin)** — no sub-agents yet.
6. **No mobile app, no own inventory, no own payment gateway, no lending** in early phases.

---

## 3. V1 (small) — tighten the plan without growing scope

Small structural and flow clarifications that make V1 easier to build and pilot.

### 3.1 Quote expiry & price validity window
**Idea:** Every quote stores `valid_until` (e.g. 2–6 hours or end of day), aligned with how long supplier fares are typically holdable.  
**Why:** Agents and customers treat old quotes as live; expired prices cause failed bookings and support load.  
**Flow change:** `draft → sent → paid → expired` already exists — make expiry first-class (cron/job marks expired; WhatsApp send blocked on expired quotes; agent can “re-search & refresh quote”).  
**Effort:** Low–medium. **Priority:** High for pilot quality.

### 3.2 Passenger data capture before payment
**Idea:** Collect passenger names / DOB / passport (as required by product type) on the quote *before* sending the payment link — or on a short “complete booking details” step after pay but before supplier confirm.  
**Why:** Supplier booking APIs need pax details; collecting only after pay creates race conditions and failed confirms.  
**Recommendation:**  
- Flights: collect pax before pay (or immediately after pay, with booking held as `pending_pax` if supplier allows).  
- Hotels: guest name at minimum before confirm.  
**Effort:** Medium. **Priority:** High — decide in week 1–2 schema.

### 3.3 Idempotent payment → booking pipeline
**Idea:** Webhook + background job must be idempotent (`payment_id` unique; booking created at most once).  
**Why:** Gateways retry webhooks; double-booking is catastrophic.  
**Effort:** Low if designed in from day one. **Priority:** Critical (architecture, not a “feature”).

### 3.4 Agent activity states for admin
**Idea:** Admin sees `invited → pending_approval → active → inactive`, plus last booking date.  
**Why:** Docs already say manual approve/reject; explicit states reduce confusion during pilot.  
**Effort:** Low. **Priority:** Medium.

### 3.5 Shareable quote link + WhatsApp (both)
**Idea:** V1 generates a hosted quote page (link) *and* sends WhatsApp summary + same link + pay link. PDF optional later.  
**Why:** Hosted link is easier to update/expire than PDF; WhatsApp is the delivery channel agents already use.  
**Effort:** Medium (already roughly in plan). **Priority:** Prefer link-first over PDF-first.

### 3.6 Minimal audit log
**Idea:** Append-only log for: quote sent, payment received, booking confirmed/failed, cancel requested.  
**Why:** Pilot support (“what happened to Rahul’s booking?”) without a full ops tool.  
**Effort:** Low. **Priority:** Medium–high for pilot.

### 3.7 Failure states that are honest
**Idea:** Explicit statuses: `booking_failed`, `payment_received_booking_pending`, `needs_manual_support`. Surface these in agent + admin UI.  
**Why:** Plan already says V1 cancellations/refunds can be manual — failed *confirms* will still happen. Don’t hide them.  
**Effort:** Low–medium. **Priority:** High.

---

## 4. Flow improvements (same product, cleaner path)

### 4.1 “Working draft” before customer quote
**Current distilled flow:** search → select → margin → quote → send.  
**Enhancement:** Allow agent to park multiple options in a **comparison tray** (2–3 flights / hotels), then pick one to quote.  
**Why:** Real agents compare options in WhatsApp drafts; one-shot select feels rigid.  
**Phase:** **V1.5** (if pilot agents ask for it) or light **V1 (small)** if tray is just client-side + one quote still saved.

### 4.2 Re-quote / clone quote
**Idea:** From an expired or unpaid quote → “Refresh search with same params” and clone margin/customer.  
**Why:** Most follow-ups are re-quotes, not brand-new searches.  
**Phase:** **V1.5 / V2**.

### 4.3 Payment success UX for customer
**Idea:** After pay, customer landing page: “Payment received — tickets/voucher will be sent on WhatsApp.” Then WhatsApp confirmation with PNR/voucher when supplier confirms.  
**Why:** Gap between pay and supplier confirm can be minutes; silence creates panic calls to the agent.  
**Phase:** **V1 (small)**.

### 4.4 Agent-side “booking desk” queue
**Idea:** Simple list: `Needs attention` (paid but not confirmed, cancel requests, expired with interest).  
**Why:** Agents won’t dig through CRM when something breaks.  
**Phase:** **V1.5**.

### 4.5 Separate “customer price” from “agent cost” everywhere
**Idea:** UI and DB always show: supplier cost (agent-only), markup, customer total, estimated commission. Never show supplier cost on customer quote.  
**Why:** Prevents accidental margin leaks on shareable links.  
**Phase:** **V1 (small)** — structural, do from day one.

---

## 5. Structural / architecture enhancements

### 5.1 Organization model ready for white-label (without building white-label)
**Idea:** `organizations` table includes nullable fields early: `slug`, `brand_name`, `logo_url`, `primary_color` (unused in V1 UI except maybe quote header = agency name).  
**Why:** White-label (V3) becomes config + theming, not a schema rewrite.  
**Phase:** **V1 (small)** schema only.

### 5.2 Optional `parent_organization_id` (unused until V3)
**Idea:** Nullable self-FK on organizations for future distributor hierarchy. No UI, no commission split logic.  
**Why:** Avoids painful migration later; costs almost nothing now.  
**Phase:** **V1 (small)** schema only — **do not implement hierarchy logic**.

### 5.3 Supplier adapter contract (freeze early)
**Idea:** Freeze interface + normalized DTOs in writing before coding TBO/TripJack:

```text
search_flights / search_hotels
price_lock or revalidate (if supplier supports)
create_booking / cancel_booking / get_booking_status
```

**Enhancement vs plan:** Add an explicit **`revalidate_fare(quote_id)`** (or equivalent) step before payment link creation and again before supplier confirm.  
**Why:** Fares change; paying on a stale quote is a top failure mode.  
**Phase:** **V1** — treat as part of Search/Booking, not optional polish.

### 5.4 Outbox / job table for async work
**Idea:** Persist intended side effects (`send_whatsapp`, `confirm_booking`, `send_payment_confirmation`) as jobs with status, retries, and last_error.  
**Why:** More reliable than “fire and forget” Celery alone; admin can replay failed jobs.  
**Phase:** **V1 (small)** structural.

### 5.5 Config-driven supplier credentials per environment
**Idea:** `suppliers` + `supplier_credentials` (already in plan) with clear sandbox vs production flags; never hardcode.  
**Phase:** **V1**.

### 5.6 AI as a separate service (already in work-division) — keep the contract thin
**Enhancement:** Define versioned contracts early even if stubs return mocks:

- `POST /ai/parse-intent`
- `POST /ai/format-quote-draft`

Optional later: `POST /ai/rank-options` (within budget).  
**Phase:** Contract in **V1**; implementation **V2** (**Farhan**).

---

## 6. Feature enhancements by phase

### 6.1 V1.5 — pilot friction killers (after first real bookings)

| Idea | Why it matters |
|---|---|
| Quote templates (short WhatsApp text presets) | Agents rewrite the same message 20×/day |
| Duplicate customer merge / phone uniqueness per org | CRM gets messy fast |
| Basic filters on bookings (date, status, customer) | Admin + agent support |
| Manual “mark as paid offline” (cash/UPI outside gateway) with audit | Many Indian agencies still take offline payment |
| Export bookings CSV (per agent / date range) | Accountants still live in Excel |
| Rate-limit + search abuse protection per agent | Protects supplier quota |

### 6.2 V2 — strengthen what the plan already lists

| Plan item | Suggested enhancement |
|---|---|
| AI Copilot | Add “within budget” ranking + explain “why these 3 options”; always show raw supplier refs for agent trust |
| Packages | Version packages (`v1`, `v2`); retire old ones without breaking past quotes |
| Commission & Wallet | Distinguish **platform fee** vs **agent markup** vs **supplier payout**; statement PDF monthly |
| Follow-up automation | Let agent snooze / “customer said later”; don’t spam; optional customer-facing reminder template |

**Additional V2 ideas (not in master plan, worth considering):**

1. **Fare calendar / flexible dates (±3 days)** — agents often need “cheapest nearby date.”  
2. **Multi-city / return clarity in search UX** — even if API supports it, UI must not bury it.  
3. **Document vault per booking** — tickets, vouchers, invoices stored and re-sendable on WhatsApp.  
4. **Agent notes on customer** (“prefers morning flights”, “visa pending”) — lightweight, high retention.  
5. **Quote analytics for agent** — sent / viewed / paid conversion (view requires hosted quote page).  
6. **Role: “ops” inside agency** — same org, can book but maybe can’t change margins (prep for larger agencies; still flat, not hierarchy).

### 6.3 V3 — clarify white-label, second supplier, hierarchy

#### White-label (make the concept concrete)
**What it is:** Same TripOS engine; each organization can expose a **branded customer surface**:
- Custom domain (`book.agencyname.com`)
- Logo, colors, agency name on quote + payment success pages
- Optional public “request a trip” form that creates a lead in that org’s CRM

**What it is not:** A separate codebase, separate supplier contract per brand (unless commercially required), or a consumer super-app.

**Suggested build slices:**
1. Branding on hosted quote + WhatsApp footer (“Powered by {Agency}”)  
2. Custom domain + TLS  
3. Optional public lead / soft-search page  
4. Remove or minimize “TripOS” branding for paying white-label tenants  

#### Second supplier
**Enhancement detail:**
- Adapter registry: `SupplierA`, `SupplierB`
- Search strategy config: `primary_only` → `failover` → `merge_and_dedupe` (merge is hardest; start with failover)
- Per-route or per-product supplier preference (flights on A, hotels on B) if commercials differ  
- Unified booking record stores `supplier_code` + `supplier_booking_ref`

#### Distributor hierarchy
**Enhancement detail (when you get there):**
- Org tree: master → sub-agents  
- Permission scopes: sub sees only own customers/bookings  
- Commission waterfall rules (configurable %, not hardcoded)  
- Credit / limit at master level (Park until Nilesh defines commercial model — do not invent lending)

---

## 7. New ideas worth parking (or sequencing carefully)

These can differentiate TripOS later but are easy to build too early.

| Idea | Notes | Suggest phase |
|---|---|---|
| Inbound WhatsApp (“customer replies YES”) | Needs templates, mapping, human takeover | V3 / Park |
| Visa / insurance add-ons at quote time | High attach revenue; needs partners | V2–V3 |
| Group / series bookings | Different workflow from FIT | Park |
| Agent mobile PWA (not native app) | Installable dashboard for on-the-go | V2 |
| Multi-currency | Only if Nilesh’s supply needs it | Park |
| Customer login portal | Usually unnecessary if WhatsApp + link works | Park |
| Automated refunds end-to-end | Supplier rules vary; dangerous early | After V2 wallet |
| Voice notes → AI intent | Nice for agents; same AI boundary | V3 |
| Lead inbox from Instagram/FB | Marketing channel, not core loop | Park |
| SLA timers for ops on `booking_failed` | Helps Nilesh’s team at volume | V2–V3 |

---

## 8. Commercial / product policy enhancements (need Nilesh input)

Not engineering-first — but they change schema and flows if ignored:

1. **Who holds the customer money?** Platform merchant account vs agent-wise sub-accounts (Razorpay Route / similar).  
2. **When does supplier get paid / credit used?** Affects when you can safely auto-confirm.  
3. **Cancellation window copy** on quote page (even if process is manual in V1).  
4. **GST / invoice** — who issues invoice to customer (agent vs platform).  
5. **Default markup caps or suggested markup** — optional guardrails so new agents don’t underprice.

**Action:** Schedule a 60-minute commercial checklist with Nilesh before Payments module is finalized.

---

## 9. UX / trust enhancements (high leverage, easy to underestimate)

1. **Plain-language quote page** — dates, airline/hotel name, inclusions/exclusions, total in ₹, expiry time, pay CTA. No GDS jargon.  
2. **Always show “price may change until paid”** if revalidation isn’t instant.  
3. **Agent preview** of WhatsApp message before send.  
4. **Empty states that teach the loop** — first login: “Create customer → Search → Quote → Send.”  
5. **Hindi WhatsApp templates before Hindi full UI** — matches master plan; do templates in V1 if Meta approval allows.

---

## 10. Suggested priority stack (for planning workshops)

Use this order when converting enhancements into the execution plan:

### Must decide before / during V1 build
1. Fare revalidation before pay + before confirm  
2. When passenger details are collected  
3. Idempotent payment → booking jobs + failure statuses  
4. Hosted quote link (link-first)  
5. Org fields for future brand + optional parent_org_id  
6. Commercial: money flow + invoicing (Nilesh)

### Strong V1.5 candidates (after pilot week 1–2)
1. Offline payment mark  
2. Re-quote / refresh  
3. Needs-attention queue  
4. CSV export  
5. WhatsApp message presets  

### Confirm for V2 roadmap (after 10–20 active agents)
1. AI Copilot behind frozen API contract  
2. Packages + document vault  
3. Wallet/commission statements  
4. Follow-ups with snooze  
5. Quote view/pay analytics  

### Explicitly later (V3)
1. White-label domains  
2. Second supplier (failover first, merge later)  
3. Distributor hierarchy + commission waterfall  

---

## 11. Acceptance checklist (team review)

For each item you care about, mark:

- [ ] **Accept for V1**
- [ ] **Accept for V1.5**
- [ ] **Accept for V2 / V3**
- [ ] **Park**
- [ ] **Reject** (with one-line reason)

Minimum recommended accepts (engineering judgment):

| Item | Suggested vote |
|---|---|
| Revalidate fare before pay/confirm | Accept V1 |
| Idempotent webhook + job outbox | Accept V1 |
| Honest failure statuses | Accept V1 |
| Hosted quote link-first | Accept V1 |
| Org branding fields + parent_org_id (schema only) | Accept V1 |
| Pax data timing decision | Accept V1 (decide, then build) |
| Offline paid + re-quote | Accept V1.5 |
| White-label / 2nd supplier / hierarchy logic | Keep V3 (schema hooks only now) |

---

## 12. Next step after this document

Once this file is reviewed and items are voted:

1. Execute using **`tripos-master-plan.md`** (40-phase checklist) — this replaced the old idea of a separate `tripos-execution-plan.md`.
2. Keep **work division** current — Farhan builds all code/AI; Sahil/Nilesh supply API access.
3. Only then start repo scaffolding (Auth + schema + supplier interface stubs).

**Do not start coding V2/V3 features from this list until V1 core loop is live with pilot agents.**

**Note (2026-09-16):** Critical items from `tripos_plan_review.md` (pax-before-pay, pricing columns, failure_reasons, wa.me, auth BFF, etc.) are now locked in `tripos-implementation-plan.md` §0.1 and the master plan.
