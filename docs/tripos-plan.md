# TripOS — B2B Travel Agent Operating System
### Complete Plan: The Idea, The Build, The Execution

 Farhan (Product & Engineering — **full build including AI**) + Sahil (API credentials / access sourcing only) + Nilesh Yashwantrao (Travel Industry, Licensing, Supply, Distribution, API relationships)
**Status:** Pre-build, assets confirmed, ready to scope V1

---

## 1. The One-Line Idea

**A software platform that lets travel agents search flights/hotels/packages, generate a customer quote, send it on WhatsApp, and get paid — all from one dashboard — with AI used to speed up the quoting step, not to replace the booking engine.**

You are not building a consumer travel site. You are not competing with MakeMyTrip. You are building **software that agents pay to use**, and (later) taking a cut of the transactions that flow through it.

---

## 2. Why This Is Buildable Now (and wasn't, on paper alone)

Every version of this idea lives or dies on three things. You have all three:

| Requirement | Status |
|---|---|
| Legal ability to sell travel (IATA / TAAI / FAAT / Aviation license) | **Held** |
| Supplier inventory access (TBO/TripJack-type B2B API) | **Nilesh sir has it / will provide it** |
| A first set of agents to actually use the product | **Nilesh sir's existing agent network** |

This changes the plan materially from a generic "validate on a spreadsheet first" startup playbook. You can build the real thing from day one, because the two hardest non-technical blockers — regulatory standing and supplier access — are already solved. The only thing left to prove is: **will agents actually use it, and will it be good enough that they keep using it.**

---

## 3. Who Does What

Be explicit about this early — most two-founder travel-tech ventures fail on ambiguity here, not on code.

**Nilesh sir and Sahil Shah:**
- Supplier relationship & API contract (TBO/TripJack) — commercial terms, credit lines, margin structure
- Compliance (IATA/TAAI/FAAT/Aviation obligations, refund/cancellation policy per supplier rules)
- Agent acquisition — bringing the first 10–20 agents from his existing network
- Pricing/commercial judgment (what margin is realistic per booking type, what agents will actually pay)

**Farhan:**
- Product design and full build (frontend, backend, integrations)
- Technical decisions (stack, architecture, hosting)
- Turning agent feedback into the roadmap


---

## 4. The Product

### 4.1 Who it's for (ICP)

Small to mid-sized Indian travel agencies (1–20 people) who already sell flights/hotels/packages but run their business across WhatsApp, Excel, and multiple supplier logins. They already understand travel software — you're not educating a new market, you're replacing a fragmented one.

### 4.2 The core workflow (this is the whole product, distilled)

```
Agent logs in
   → Searches flight/hotel (via TBO/TripJack API)
   → Selects options, sets their margin
   → System generates a customer-facing quote
   → Sends quote on WhatsApp with a payment link
   → Customer pays
   → Booking confirms automatically
   → Booking + customer saved to CRM
```

If this one flow works end-to-end and an agent actually uses it instead of Excel + manual WhatsApp, you have a product. Everything else is expansion.

### 4.3 V1 scope — build this, nothing more

- **Auth & agent onboarding** — login, basic KYC, single organization per agent (no sub-agents yet)
- **Flight search & booking** — one supplier integration (TBO or TripJack, whichever Nilesh's agreement covers first)
- **Hotel search & booking** — same supplier if possible, to avoid a second integration in V1
- **Quotation builder** — agent picks flight/hotel, sets margin, system generates a clean customer-facing quote (PDF or shareable link)
- **WhatsApp share** — quote + payment link via **wa.me** (agent sends from their WhatsApp); upgrade to Business/Cloud API later
- **Payment link** — Razorpay/PayU/similar; do not build your own payment handling
- **Basic CRM** — customer name, phone, booking history, nothing more elaborate
- **Admin view** — Nilesh/you can see all agents, all bookings, commission owed

**Explicitly not in V1:** AI quoting, holiday packages, white-label, wallet/credit system, sub-agent hierarchies, multi-language, mobile app. All of these are real, but they're V2+.

### 4.4 V2 — after 10–20 agents are actively booking

- AI-assisted quote generation: agent types "4 pax, Mumbai–Dubai, 5N Dec, budget 2L" → system runs the actual search APIs and drafts a quote for the agent to review and send. **The AI never invents prices or availability — it only orchestrates real API calls and formats the result.**
- Holiday packages (admin-curated packages agents can resell as-is)
- Agent wallet + commission auto-calculation
- Basic follow-up reminders (quote sent, no payment in 24h → nudge agent)

### 4.5 V3 — after real transaction volume (100+ agents)

- Second supplier integration for redundancy/better pricing
- White-label storefronts for agencies who want their own branded booking page
- Sub-agent / distributor hierarchy
- Multi-language WhatsApp/AI (Hindi first, then Marathi given your Mumbai/Maharashtra base)

---

## 5. Technical Architecture

### 5.1 Stack (updated — see `tripos-implementation-plan.md` for full lock)

- **Frontend:** Next.js + TypeScript on **Vercel**
- **Backend:** FastAPI (Python) on **Render**
- **Database:** PostgreSQL
- **Cache (when needed):** **Upstash Redis**
- **Email / verification:** **Resend**
- **WhatsApp (V1):** **wa.me** deep links (Business API later)
- **Payments:** Razorpay/PayU
- **Background jobs:** Celery (Render worker) when required

Build this as **one FastAPI service (modular monolith)**, not microservices.

### 5.2 High-level flow

```
Next.js dashboard
      │
      ▼
FastAPI (single service)
   ├── auth
   ├── agents
   ├── customers (CRM)
   ├── search  ──────► Supplier abstraction layer ──► TBO/TripJack API
   ├── bookings
   ├── quotes
   ├── payments ─────► Razorpay/PayU
   └── whatsapp ─────► wa.me links (V1) → Cloud API later
      │
      ▼
PostgreSQL + Upstash Redis (when needed)
```

### 5.3 Core database tables (V1)

```
users, agents, agent_users
customers
searches (cached)
quotes, quote_items
bookings, booking_passengers
payments, refunds
commissions
suppliers, supplier_credentials
messages (WhatsApp log)
```

### 5.4 The one architectural rule that matters

**Never let the supplier API be called directly from application logic scattered across the codebase.** Build one interface:

```python
search_flights(origin, destination, dates, pax)
search_hotels(city, dates, rooms)
create_booking(quote_id)
cancel_booking(booking_id)
get_booking_status(booking_id)
```

Everything else calls these functions. When you add a second supplier later (V3), you swap the implementation behind this interface without touching the rest of the app.

### 5.5 Where AI actually belongs (and where it doesn't)

AI is a UX layer over real data, never a source of truth for price or availability:

```
Agent types natural language request
      ↓
LLM extracts structured intent (dates, pax, budget, destination)
      ↓
Your backend calls search_flights() / search_hotels() — real API calls
      ↓
LLM formats the real results into a readable quote draft
      ↓
Agent reviews and sends
```

Build this in V2, not V1. In V1, the agent uses normal search filters — that's faster to build and good enough to prove the core loop works.

---

## 6. WhatsApp Flow (V1)

**V1 uses wa.me links** — no Meta Cloud API required to start.

```
Agent clicks "Send to Customer"
      ↓
System builds message text + hosted quote URL + payment URL
      ↓
Opens: https://wa.me/<customer_phone>?text=<urlencoded message>
      ↓
Agent sends from their WhatsApp
      ↓
Customer taps pay → Razorpay/PayU → webhook → booking auto-confirms
```

**Later (V2/V3):** swap to WhatsApp Business Cloud API or Interakt/AiSensy for true server-side send + templates. Keep the Messaging module swappable so Quote/Payments do not change.

---

## 7. Business Model

**Priority order — transaction revenue first, subscriptions later:**

1. **Transaction margin/commission** — your primary revenue engine from day one. A small markup or share of agent commission on every booking.
2. **SaaS subscription** — once agents are dependent on the CRM/quoting workflow (roughly V2+), introduce a paid tier (₹1,500–2,500/month) for CRM, WhatsApp automation, and AI quoting. Keep basic search/booking free to remove adoption friction.
3. **Later (not now):** white-label fees, API access for third parties, financial services (credit/insurance) via a regulated partner — never lend from your own balance sheet.

Don't build a 4-tier pricing page yet. You don't have enough usage data to price this correctly until agents are actually transacting.

---

## 8. Go-to-Market

Because Nilesh already has an agent network, skip the generic "cold-call 500 agents" playbook — that's for founders without one.

1. **Pilot group:** 5–10 agents from Nilesh's existing relationships. Give them free/low-cost access in exchange for weekly feedback.
2. **Watch, don't assume:** sit with 2–3 of them and watch how they currently quote and follow up with customers. Build V1 around what you actually see, not what the blueprint documents assumed.
3. **Expand only after the core loop sticks:** an agent counts as "active" only if they've made a real booking through the platform, not just logged in. Target: 20 active agents before adding any V2 feature.
4. **Geography:** stay in Mumbai/Maharashtra initially — easier for Nilesh to support relationships in person, easier for you to debug issues quickly.

---

## 9. Execution Timeline

**Weeks 1–2 — Foundation**
- Finalize equity/role split in writing
- Nilesh: lock supplier API credentials, confirm which supplier (TBO or TripJack) goes live first
- Farhan: repo setup, auth, agent onboarding skeleton, DB schema

**Weeks 3–6 — Core booking loop**
- Flight search + booking integration
- Hotel search + booking integration
- Quotation builder (basic PDF/link generation)

**Weeks 7–8 — Money and messaging**
- Payment gateway integration
- WhatsApp send integration
- Basic CRM (customer + booking history)

**Weeks 9–10 — Pilot**
- Onboard 5–10 agents from Nilesh's network
- You personally watch their first 10 bookings each — fix friction immediately

**Weeks 11–12 — Decide**
- Are agents booking through it without you pushing them to? If yes → proceed to V2 (AI quoting, packages, commission automation). If no → find out why before adding a single new feature.

**Months 4–6 — V2**
- AI-assisted quoting, holiday packages, wallet/commission automation, follow-up reminders
- Target: 20–50 active agents

**Months 7–12 — Scale**
- Second supplier (redundancy/pricing), white-label option for larger agencies, sub-agent hierarchy
- Target: 100+ active agents, based on pilot learnings — treat this as a target, not a forecast

---

## 10. What NOT to Build Early

- Your own flight/hotel inventory
- Your own payment gateway
- A mobile app (web dashboard is enough for agents at a desk/laptop)
- A general AI chatbot before the booking engine works
- Multi-language UI (start English/Hindi; AI/WhatsApp can go multilingual before the full UI does)
- Any lending/credit product on your own balance sheet
- Microservices — one FastAPI service is enough until volume proves otherwise

---

## 11. Risks & What to Watch

| Risk | Mitigation |
|---|---|
| Supplier API terms change or margins are thinner than expected | Nilesh confirms actual commercial terms before V1 build starts, not after |
| Agents keep using WhatsApp+Excel out of habit | Pilot with agents Nilesh already has trust with; watch their real workflow before building |
| Booking/refund edge cases (cancellations, reissues) eat engineering time | Scope V1 to new bookings only; handle cancellation/refund status as "contact support" manually at first, automate later |
| Two-founder ambiguity on equity/effort | Put the split in writing before serious build time goes in |

---

## 12. Success Metric

Ignore signups, downloads, and demos. Track one number:

**Monthly Active Transacting Agents** — an agent counts only if they completed a real, paid booking through the platform that month.

Secondary: GMV per active agent.

---

## 13. Immediate Next Steps (This Week)

1. Nilesh sir: confirm and share the specific supplier API credentials/sandbox (TBO or TripJack — whichever is ready first)
2. Nilesh sir: shortlist the first 5 agents from his network for the pilot
3. Farhan: set up repo, DB schema, and auth skeleton
