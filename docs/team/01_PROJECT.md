# TripOS — Project Document

**Document type:** Project overview  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  
**Status:** Living summary (aligned to current repo)

---

## 1. What is TripOS?

TripOS is a **B2B travel Agent Operating System** for Indian travel agencies. It lets agents:

1. Search flights (and hotels where inventory allows)  
2. Build **margin quotes** for customers  
3. Share a branded link (WhatsApp / `wa.me`)  
4. Collect payment  
5. Automatically confirm supplier bookings  
6. Track bookings, wallet, customers (CRM), and ops attention  

TripOS is **not** a consumer OTA (not MakeMyTrip / Booking.com for end travelers). Customers only see a **public quote/pay** page; the agency manages the customer relationship.

---

## 2. Problem statement

Small and mid-size agencies (typically 1–20 people) run on:

- WhatsApp + Excel  
- Multiple supplier logins  
- Manual markup and payment chasing  
- No single place for “paid but not booked” or failed bookings  

TripOS replaces that fragmented stack with **one workspace**.

---

## 3. Goals & success metric

| Goal | Description |
|---|---|
| Primary loop | Search → Quote → Send → Pay → Book → CRM |
| Success metric | Monthly Active **Transacting** Agents |
| V1 WhatsApp | `wa.me` deep links (Cloud API later) |
| Inventory honesty | Clear **Live / Simulated / Mock** labels |

---

## 4. Scope of work completed (engineering)

Summarized from Flight Commerce (FC) and live-inventory readiness work in-repo:

| Track | Status |
|---|---|
| Monorepo (web + API + worker path) | Done |
| Auth, orgs, CRM, quotes, payments (mock), bookings outbox | Done |
| Inventory adapters: `mock_supplier` + `tbo` (sim/live gated) | Done |
| L2B shopping cache + meters + survival soft-brakes | Engineering closed |
| FC phases 2–8 scaffolds (fare rules, FX display, EN/HI, ancillaries, partner API, etc.) | Shipped (engineering) |
| Frontend UI enhancement toward NewUIReference | In progress / largely built |
| Postman API handoff pack | Done (`docs/postman/TripOS_API_Handoff/`) |

### Explicitly open / external

- Live TBO staging E2E with supplier credentials  
- Hosted smoke (Render / Vercel) sign-off  
- Commercial path for second supplier (e.g. TripJack) when needed  
- Razorpay **real** test capture (beyond mock)  
- Production document vault (R2/S3)  

### Explicitly deferred / waived

- Second **live** supplier for FC Phase 3 (waiver active; TBO primary)  
- B2C storefront inside TripOS (Partner API is the B2C-facing surface)  
- Travclan Volt integration (reviewed; **not in current plan**)  

---

## 5. Repository layout

```text
TripOS/
├── apps/web      # Next.js agent + admin + public UI
├── apps/api      # FastAPI + worker entry (outbox)
├── apps/worker  # Worker packaging / docs
├── apps/ai      # AI-related packaging
├── adapters/    # Reserved extract; live code in apps/api/app/adapters
├── docs/        # Plans, architecture, ops, this team pack
└── docker-compose.yml
```

---

## 6. How to demo / hand off testing

1. Local runbook (see System doc)  
2. Seed user: `admin@tripos.in` / `password123`  
3. Postman: `docs/postman/TripOS_API_Handoff/` — start with **Happy Path Runner**  
4. Agent UI: `http://localhost:3000` after `npm run dev`  

---

## 7. Document control

| Field | Value |
|---|---|
| Classification | Internal team |
| Sources | Root README, `docs/tripos-plan.md`, FC implementation plan, L2B readiness docs, agent-quickstart |

---

*Prepared and researched by Farhan Sayed.*
