# Pilot demo script (15–20 min)

**Owners:** Farhan (product) + Nilesh (relationship)  
**Goal:** One successful Search → Quote → Send → (mock/test) Pay loop on a shared screen.

---

## 0. Setup (5 min before call)

- [ ] Agency org created + **approved** in Admin
- [ ] Agent user can log in
- [ ] Confirm `PAYMENTS_MODE` / inventory mode with Farhan (mock vs Razorpay test)
- [ ] Send [`agent-quickstart.md`](./agent-quickstart.md) link or PDF export
- [ ] Join Pilot Support WhatsApp (see [`pilot-support-channel.md`](./pilot-support-channel.md))

## 1. Agenda (say this)

> “We’ll search a flight, build a quote with your markup, send a WhatsApp link, and see what happens when the customer pays. Then I’ll show you where failures show up.”

## 2. Walkthrough

| Min | Step | Show |
|---|---|---|
| 0–2 | Login + Home | Attention strip (empty is fine) |
| 2–5 | Search | One DEL→BOM (or their usual route) |
| 5–8 | Customer + quote | Markup + passengers + Ready |
| 8–11 | Send | WhatsApp preview / send; open `/q/{token}` as customer |
| 11–15 | Pay | Mock/test pay **or** offline mark-paid if training |
| 15–18 | Booking | Bookings list → open quote for PNR / failure banner |
| 18–20 | Failures | If mock fail available: Home attention + Support path |

## 3. Closing asks

1. Preferred first real booking date  
2. Who else on their team needs a login  
3. Any friction **now** → log in [`pilot-onboarding-tracker.md`](./pilot-onboarding-tracker.md) §2  

## 4. Do not claim

- Live airline tickets if `INVENTORY_SUPPLIERS` is mock-only / simulated TBO  
- Automatic refunds inside TripOS  
- Phase 25 “real TBO sandbox” unless Sahil credentials + live HTTP are on  

## 5. After the call

- Update tracker shortlist row (demo date, notes)  
- Add friction rows the same day  
- If they will take real money: confirm Sprint I capture + hosted smoke already done  
