# TripOS — Module Breakdown & System Flow

### Companion to `tripos-plan.md` (vision) and **`tripos-master-plan.md`** (execution checklist)

This document answers: what exactly is in each module, and how do they talk to each other.  
**If build order or WhatsApp/auth details conflict with the master plan / docs-index, those win.**

---

## 1. Module List at a Glance

| # | Module | Phase | One-line purpose |
|---|---|---|---|
| 1 | Auth & Organization | V1 | Agent login, org setup, roles |
| 2 | Admin module | V1 | Platform admin view/control over all agents (folder: `modules/admin`) |
| 3 | Customer CRM | V1 | Store customer + booking history per agent |
| 4 | Search | V1 | Query supplier API for flights/hotels |
| 5 | Quotation Engine | V1 | Turn search results + margin into a customer quote |
| 6 | Booking Engine | V1 | Confirm, track, cancel bookings with supplier |
| 7 | Payments | V1 | Generate payment link, handle webhook, reconcile |
| 8 | WhatsApp Messaging | V1 | Send quote/payment link, log conversation |
| 9 | Commission & Wallet | V2 | Auto-calculate agent commission, track balances |
| 10 | Packages | V2 | Admin-curated holiday packages agents can resell |
| 11 | AI Copilot | V2 | Natural-language quote drafting over real search data |
| 12 | Follow-up Automation | V2 | Detect unpaid quotes, nudge agent to follow up |
| 13 | White-label | V3 | Branded storefront per agency |
| 14 | Distributor Hierarchy | V3 | Sub-agents under a master agent/distributor |
| 15 | Admin/Ops Dashboard | V1→V3 | Cross-cutting visibility; grows with each phase |

Modules 1–8 are the entire V1 build. Nothing else matters until those work end-to-end.

---

## 2. Module Specs

### 2.1 Auth & Organization — `V1`

**Purpose:** Every agent belongs to an organization (their agency). This module handles who can log in and what they can see.

**Features:**
- Agent/agency signup (basic KYC fields: business name, phone, license number)
- Login (**V1: email + password only**; phone OTP is V1.5/V2 if pilot demands it)
- Email verification via Resend
- Single role in V1: "agent" and "admin" (you/Nilesh). Sub-agent roles come in V3.
- Session / token management

**Owns (data):** `organizations`, `users`, `organization_members`, `sessions` (and email verification records as needed)

**Depends on:** nothing (foundation module)

**Exposes to:** every other module — all of them check "who is this agent" before doing anything

---

### 2.2 Admin module — `V1` (canonical folder: `modules/admin`)

**Purpose:** Your (and Nilesh's) internal view to see every agent, their activity, and step in when something breaks.  
*(Formerly called “Agent Management (Admin)” in early drafts — use **Admin module** everywhere.)*

**Features:**
- List all agents, signup date, activity status
- View any agent's bookings/quotes (support access)
- Manually approve/reject new agent signups (V1 — no self-serve approval yet, you want to know who's on the platform)

**Owns (data):** reads from `organizations`, `users`, `bookings` — doesn't own new data itself

**Depends on:** Auth module

**Exposes to:** nothing (this is a consumer of other modules' data, not a producer)

---

### 2.3 Customer CRM — `V1`

**Purpose:** Every customer an agent has ever quoted or booked, in one place, replacing the agent's personal WhatsApp/Excel record.

**Features:**
- Add/view customer (name, phone, email)
- See a customer's full history: past quotes, past bookings, payment status
- Search customers by name/phone

**Owns (data):** `customers`, linked to `organizations`

**Depends on:** Auth module

**Exposes to:** Quotation Engine (a quote is always tied to a customer), WhatsApp Module (needs the customer's phone number)

---

### 2.4 Search — `V1`

**Purpose:** The only module allowed to talk to the supplier API (TBO/TripJack). Everything else asks this module for results — nothing else calls the supplier directly.

**Features:**
- Flight search (origin, destination, dates, passengers)
- Hotel search (city, dates, rooms, guests)
- Result caching (Redis) to avoid redundant supplier calls
- Normalized output — regardless of which supplier is behind it, the rest of the app sees the same result shape

**Owns (data):** `searches` (cached results, short TTL)

**Depends on:** Auth module (know which agent is searching, for rate limits/logging)

**Exposes to:** Quotation Engine (search results become quote line items), AI Copilot in V2 (calls this module instead of the raw supplier API)

**This is the module to build most carefully.** Every other module treats it as a black box: `search_flights(...)`, `search_hotels(...)`. If you get this abstraction right, adding a second supplier in V3 is a config change, not a rewrite.

---

### 2.5 Quotation Engine — `V1`

**Purpose:** Turn selected search results + agent's margin into a customer-facing quote.

**Features:**
- Agent selects flight/hotel from search results
- Agent sets their markup (₹ or %)
- System calculates final customer price
- Generates a shareable quote (PDF or hosted link) with a clean, non-technical presentation
- Quote has a status: draft → sent → paid → expired

**Owns (data):** `quotes`, `quote_items`

**Depends on:** Search (for line items), CRM (for the customer it's addressed to)

**Exposes to:** WhatsApp Module (sends the quote link), Booking Engine (a paid quote becomes a booking), Follow-up Automation in V2 (watches quote status)

---

### 2.6 Booking Engine — `V1`

**Purpose:** Once a quote is paid, actually confirm the booking with the supplier and track its lifecycle.

**Features:**
- Confirm booking with supplier API on successful payment
- Store booking reference, ticket/voucher details
- Basic status tracking: confirmed / cancelled (full amendment/reissue workflows are V2+ — in V1, anything beyond a clean cancellation is handled manually by Nilesh's team)
- Booking history per agent and per customer

**Owns (data):** `bookings`, `booking_passengers`

**Depends on:** Search (supplier interface), Quotation Engine (a booking always originates from a paid quote), Payments (booking only confirms after payment success)

**Exposes to:** CRM (updates customer's booking history), Commission module in V2 (a confirmed booking triggers a commission calculation)

---

### 2.7 Payments — `V1`

**Purpose:** Collect money from the customer and tell the rest of the system when it's been paid. **Never store card details — the payment gateway handles that.**

**Features:**
- Generate a payment link for a given quote (Razorpay/PayU/similar)
- Receive and verify payment webhook
- Mark quote as "paid" and trigger Booking Engine
- Basic refund initiation (manual trigger in V1, automated in V2)

**Owns (data):** `payments`, `refunds`

**Depends on:** Quotation Engine (what's being paid for)

**Exposes to:** Booking Engine (payment success triggers booking confirmation), WhatsApp Module (payment confirmation message)

---

### 2.8 WhatsApp Messaging — `V1`

**Purpose:** The channel through which the agent's customer actually receives quotes and payment links.

**V1 (locked):** Generate **wa.me** deep links (agent opens WhatsApp with prefilled text: quote summary + hosted quote URL + payment URL). No server-side send, no Meta Cloud API, no template approvals in V1.

**Architecture rule:** Build the Messaging module with a **provider interface** so V2/V3 can swap to WhatsApp Business Cloud API (or Interakt/AiSensy) without changing Quote/Payment modules.

**Features (V1):**
- Build prefilled message + wa.me URL for customer's normalized phone
- Optional “share confirmation” wa.me helper after booking confirm (still human-send)
- Log intended outbound messages against the customer/quote (visible in CRM)
- No inbound conversation handling in V1

**Owns (data):** `messages` (outbound log)

**Depends on:** Quotation Engine (what to send), CRM (who to send it to — normalized phone), Payments (pay URL on message)

**Exposes to:** nothing further in V1 (Cloud API auto-send + inbound come later)

---

### 2.9 Commission & Wallet — `V2`

**Purpose:** Automatically calculate what each agent earns per booking and track running balances, replacing manual commission spreadsheets.

**Features:**
- Auto-calculate commission from stored quote amounts (see Flow E — correct formula)
- Agent wallet balance (earned, pending, paid out)
- Admin view of commission owed across all agents

**Owns (data):** `commissions`, `wallets`, `wallet_transactions`

**Depends on:** Booking Engine (commission triggers on confirmed booking)

**Exposes to:** Admin Dashboard

---

### 2.10 Packages — `V2`

**Purpose:** Let admin (Nilesh's team) pre-build holiday packages (e.g. "Dubai 5N/6D — ₹75,000") that agents can resell as-is instead of building a custom quote every time.

**Features:**
- Admin creates a package (bundled flight + hotel + transfers, fixed price)
- Agent browses and sends a package to a customer with one click
- Package becomes a quote automatically

**Owns (data):** `packages`, `package_items`

**Depends on:** Search (packages are still built from real supplier data), Quotation Engine (a package sent to a customer is just a pre-filled quote)

---

### 2.11 AI Copilot — `V2`

**Purpose:** Let an agent describe a trip in plain language instead of manually filling search filters. **The AI only orchestrates the Search module — it never invents a price or availability.**

**Features:**
- Agent types: "4 pax, Mumbai–Dubai, 5N Dec, budget 2L"
- LLM extracts structured parameters
- System calls the real `search_flights()` / `search_hotels()` functions
- LLM formats the real results into a draft quote for the agent to review

**Owns (data):** none new — it's an orchestration layer over Search + Quotation Engine

**Depends on:** Search, Quotation Engine

---

### 2.12 Follow-up Automation — `V2`

**Purpose:** Catch the revenue currently lost because agents forget to follow up on a sent quote.

**Features:**
- Detect: quote sent, no payment after 24h → notify agent
- Detect: no payment after 48h → second nudge
- Agent can trigger a follow-up WhatsApp message with one click

**Owns (data):** none new — reads `quotes` status over time

**Depends on:** Quotation Engine, WhatsApp Module

---

### 2.13 White-label — `V3`

**Purpose:** Let a larger agency run a branded booking page under their own domain, powered by your backend.

**Features:**
- Custom domain/branding per organization
- Agency's own customer-facing booking flow

**Depends on:** every core module above — this is a presentation layer, not new business logic

---

### 2.14 Distributor Hierarchy — `V3`

**Purpose:** Support a master agent with sub-agents under them (a real structure in Indian travel distribution).

**Features:**
- Multi-level organization structure
- Commission split across levels
- Permission scoping (sub-agent sees only their own bookings)

**Depends on:** Auth & Organization (extends the org model), Commission & Wallet

---

### 2.15 Admin/Ops Dashboard — `V1 → V3`

**Purpose:** Your and Nilesh's command center. Grows in scope with every phase but isn't a separate build effort — it's a read layer over everything else.

**V1:** agent list, booking list, basic revenue view
**V2:** commission owed, package performance, follow-up effectiveness
**V3:** distributor tree view, white-label tenant management

---

## 3. End-to-End Flows

### Flow A — The Core Loop (V1): Search to Confirmed Booking

```
Agent logs in (Auth)
   │
   ▼
Agent searches flight/hotel (Search module → Supplier API)
   │
   ▼
Agent selects results, sets margin (Quotation Engine)
   │
   ▼
System generates customer quote, tied to a CRM customer record
   │
   ▼
Agent clicks "Send" (WhatsApp Module → customer's phone)
   │
   ▼
Customer receives quote + payment link, taps pay
   │
   ▼
Payment Gateway → webhook → Payments module marks quote "paid"
   │
   ▼
Booking Engine confirms booking with supplier API
   │
   ▼
CRM updates customer's booking history
   │
   ▼
WhatsApp Module sends payment/booking confirmation to customer
```

This entire chain is what "V1 done" means. If every arrow above works reliably, you have a real product.

---

### Flow B — Payment Webhook (async, system-level)

```
Payment Gateway (Razorpay/PayU)
      │  webhook: payment.success
      ▼
Payments module verifies signature
      │
      ▼
Marks quote.status = "paid"
      │
      ▼
Triggers Booking Engine.create_booking(quote_id)
      │
      ▼
Booking Engine calls Search module's create_booking() interface → Supplier API
      │
      ▼
On supplier confirmation → booking.status = "confirmed"
      │
      ▼
Notifies WhatsApp module to send confirmation
```

Build this as a background job (Celery/RQ), not inline in the webhook handler — supplier confirmation can be slow, and you don't want to block the webhook response.

---

### Flow C — Follow-up Automation (V2)

```
Quote sent (status = "sent")
      │
      ▼
Scheduled job checks quotes with status = "sent" older than 24h
      │
      ▼
No payment? → Notify agent: "Rahul hasn't paid for his Dubai quote"
      │
      ▼
Agent clicks "Follow up" → WhatsApp module resends with a reminder note
      │
      ▼
Still unpaid after 48h → second automated nudge to agent
```

---

### Flow D — AI-Assisted Quote (V2)

```
Agent types: "4 pax, Mumbai–Dubai, 5N Dec, budget 2L"
      │
      ▼
AI Copilot extracts: origin, destination, pax, dates, budget
      │
      ▼
Calls Search.search_flights() and Search.search_hotels() — REAL data, no invented prices
      │
      ▼
AI formats results into a draft quote within budget
      │
      ▼
Agent reviews, adjusts margin, sends (rejoins Flow A at "Quotation Engine")
```

---

### Flow E — Commission Reconciliation (V2)

**Correct money identity (store these on every quote_item from V1 even if wallet logic is V2):**

```text
customer_total = supplier_cost + agent_markup + platform_fee
total_margin   = customer_total − supplier_cost
agent_commission (typical) = agent_markup   (or total_margin − platform_fee — confirm in Phase 0)
platform_revenue           = platform_fee
```

```
Booking confirmed (Flow A/B completes)
      │
      ▼
Commission module reads stored amounts (never re-invent from “payout − price”)
      │
      ▼
agent_commission = f(agent_markup, platform_fee rules) → wallet pending
      │
      ▼
Admin dashboard shows commission owed across all agents
      │
      ▼
Periodic payout (manual in V2, automated in V3)
```

**Do not use** `supplier_payout − customer_price` — that formula is inverted and wrong.

---

## 4. Module Dependency Map

```
                        Auth & Organization
                               │
        ┌──────────┬──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
      CRM       Search   Admin module (all modules check Auth)
        │          │
        └────┬─────┘
             ▼
      Quotation Engine
             │
      ┌──────┼──────┐
      ▼             ▼
  Payments    WhatsApp Messaging
      │
      ▼
  Booking Engine ──────► Commission & Wallet (V2)
      │
      ▼
  Admin/Ops Dashboard (reads from everything)

  Packages (V2) ──────► built on Search + Quotation Engine
  AI Copilot (V2) ────► built on Search + Quotation Engine
  Follow-up (V2) ─────► built on Quotation Engine + WhatsApp
  White-label (V3) ───► presentation layer over all core modules
  Distributor (V3) ───► extends Auth & Organization + Commission
```

The pattern to notice: **Search, Quotation Engine, and Payments are the three modules everything else eventually depends on.** Build these with the most care; every later module (V2 and V3) is built on top of them, not alongside them.

---

## 5. Build Order (aligned to `tripos-master-plan.md`)

| Master phases (approx.) | Module(s) |
|---|---|
| Phases 3–6 | Auth & Organization, base DB schema |
| Phase 10 | **Customer CRM first** (quotes need a customer) |
| Phases 11–13 | Adapter platform + Inventory search (mock → UI) |
| Phases 14–17 | Quotation Engine + wa.me Messaging + public quote |
| Phases 18–22 | Payments + Outbox/worker + Booking Engine |
| Phases 23–24 | Audit + Admin module |
| Phase 25+ | First real supplier; E2E; deploy; pilot |
| Phases 32–35 (V2) | Commission & Wallet, Packages, Follow-ups, AI Copilot |
| Phases 36–38 (V3) | Multi-supplier strategies, White-label, Distributor Hierarchy |

**Canonical order:** CRM before Search/Quotes — matches the master plan (not the old week table).

---

## 6. Rough API Surface (V1)

```
POST   /auth/signup
POST   /auth/login

GET    /customers
POST   /customers

GET    /search/flights
GET    /search/hotels

POST   /quotes
GET    /quotes/{id}
POST   /quotes/{id}/send        (triggers WhatsApp)

POST   /payments/create-link
POST   /payments/webhook

POST   /bookings/confirm        (internal, triggered by payment webhook)
GET    /bookings/{id}
POST   /bookings/{id}/cancel

GET    /admin/agents
GET    /admin/bookings
```

Keep this list literal for V1 — resist adding endpoints for V2/V3 modules until their week arrives.
