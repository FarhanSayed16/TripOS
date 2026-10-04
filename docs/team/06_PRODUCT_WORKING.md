# TripOS — Product Working Document

**Document type:** How the product works (user journeys)  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. Personas

| Persona | Uses |
|---|---|
| **Agent** | Daily Search → Quote → WhatsApp → Pay → Book |
| **Org admin (agency)** | Settings, branding, domains, network/sub-agents, packages |
| **Platform admin** | Approve orgs, L2B, suppliers, partners, FX, refunds |
| **End customer** | Public quote page only (`/q/{token}`) — pay / view itinerary |

---

## 2. Master agent loop

```text
Login → Home (attention)
      → Search inventory
      → Select offer → Quote builder (markup + passengers)
      → Mark Ready → Send WhatsApp / copy public link
      → Customer pays
      → System books → Bookings ledger + PNR
```

Detailed pilot copy: `docs/agent-quickstart.md`.

---

## 3. Screen-by-screen (current product)

### 3.1 Marketing
- Landing with TripOS brand, waitlist / CTAs, feature sections.  
- Entry to Sign in / Get started.

### 3.2 Auth
- Login, signup, verify, forgot/reset password.  
- Seed for local: `admin@tripos.in` / `password123`.

### 3.3 Agent Home
- Greeting + **attention** cards (failed bookings, paid awaiting confirm).  
- KPI strip (bookings, GMV, wallet, customers).  
- Embedded search shortcut → `/app/search`.  
- Recent bookings table.  
- Right rail: wallet summary, notifications, AI promo.

### 3.4 Search
- Flights / Hotels tabs.  
- Deal code field (where enabled).  
- Results with filters, inventory mode chips, FX footnote.  
- Selected offer rail (desktop) / sticky bar (mobile) → Continue to quote.

### 3.5 Quotes
- List with status, money (mono), copy public link.  
- Detail: passengers, itinerary, **markup ladder** (supplier / fee / markup / extras / customer), WhatsApp, pay link, cancel, audit.  
- Builder: cart from selected offers → customer → passengers → ready.

### 3.6 Public quote (`/q/[token]`)
- Agency branding / theme.  
- EN / हिं toggle.  
- Itinerary + total (no agent economics).  
- Pay CTA + trust footer.  
- Validity / expired states.

### 3.7 Bookings
- KPI strip + filters + search.  
- Status, PNR, amount, Change (reissue) path with honesty banner when mock.  
- Deep link to quote for full detail.

### 3.8 Wallet / Payments
- Wallet summary + ledger / export.  
- Payments list tied to quotes.

### 3.9 Customers (CRM)
- Create / list / detail + timeline of quotes/bookings.  
- `/app/crm` redirects to customers.

### 3.10 Settings
- Tabs: Org, Display (currency/locale — wired), Deal codes, AI, Domain checklist, notifications.  
- Some tabs may be **preview** until APIs persist (labeled honestly in UI where applicable).

### 3.11 Packages / Network / AI / Followups
- Packages: curated packages → quote conversion (estimated costs honesty).  
- Network: sub-agent creation (org admin).  
- AI: intent parse / draft (flag-gated).  
- Followups: snooze / dismiss / remind.

### 3.12 Admin
- Analytics, L2B (+ survival), organizations approve/reject.  
- Bookings / payments / refunds / commissions.  
- Suppliers health + toggle.  
- FX rates.  
- Partners create/rotate keys (for Partner API).  

---

## 4. Status language agents see

| Quote status | Meaning |
|---|---|
| draft | Being built |
| ready | Passengers OK; can send / pay |
| sent | Shared to customer |
| paid | Money captured / offline marked |
| expired / cancelled | Terminal |

| Booking status | Meaning |
|---|---|
| pending | Confirm job not finished |
| confirmed | PNR available |
| failed | Needs attention / support |
| cancelled | Cancelled (soft supplier path possible) |

---

## 5. Inventory honesty in product

Agents must see source truth:

- **Live** — real supplier HTTP  
- **Simulated** — TBO-shaped but not live (`SIM-TBO…`)  
- **Mock** — `mock_supplier` practice inventory  

During early pilot, training often runs on **mock**.

---

## 6. Happy-path demo script (local)

1. Start Docker, API `:8000`, worker, web `:3000`.  
2. Login seed admin.  
3. Search DEL→BOM.  
4. Create customer + quote + markup.  
5. Passengers → Ready → Pay link.  
6. Open public `/q/...`.  
7. Mark paid offline (demo) → wait for worker → check Bookings.  
8. Optional: Postman Happy Path Runner for API-only review.  

---

## 7. What customers never see

- Supplier cost  
- Agent markup  
- Platform fee  
- Internal IDs / admin tools  

Public payload is sanitized by design.

---

*Prepared and researched by Farhan Sayed.*
