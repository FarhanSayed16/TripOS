# Pilot Onboarding Tracker (Phase 29 / Sprint N)

**Owners:** Nilesh (agency shortlist + demos) · Farhan (product/support ops)  
**Exit:** ≥3 agencies with ≥1 **real** paid booking — blocked on hosted smoke + live Razorpay (Sprint I/M).

**Related pack:**
- Quickstart → [`agent-quickstart.md`](./agent-quickstart.md)
- Demo call script → [`pilot-demo-script.md`](./pilot-demo-script.md)
- Support channel → [`pilot-support-channel.md`](./pilot-support-channel.md)
- Failures / refunds → [`ops/PAYMENT_CAPTURED_BOOKING_FAILED.md`](./ops/PAYMENT_CAPTURED_BOOKING_FAILED.md), [`ops/RAZORPAY_REFUND_SOP.md`](./ops/RAZORPAY_REFUND_SOP.md)
- Commercial → [`phase-0/COMMERCIAL_CHECKLIST.md`](./phase-0/COMMERCIAL_CHECKLIST.md)

---

## 0. Pre-pilot gates (Farhan)

| Gate | Status | Doc |
|---|---|---|
| Hosted API + worker + web | Pending secrets — smoke script ready | `ops/HOSTED_SMOKE.md`, `scripts/hosted_smoke.py` |
| Local E2E green ×2 | **Done (Sprint P)** | `e2e-runs.md` |
| Commercial checklist signed | Pending Nilesh | `phase-0/COMMERCIAL_CHECKLIST.md` |
| One Razorpay **test** capture in TripOS | Pending | `phase-0/PHASE_0_DECISIONS.md` Sprint I table |
| Mock inventory only (honest) | Default | `INVENTORY_SUPPLIERS=mock_supplier` |
| Admin Failures + Home attention | Done | Sprint K |
| Phase 31 decision | **FIX V1** until hosted + commercial + shortlist | `v1-exit-decision.md` |

Do **not** invite real money until hosted smoke + commercial (or explicit defaults ack) are green.

---

## 1. Agent shortlist & status

Nilesh fills real rows. Keep *Example* as format only.

| # | Agency | Contact | Phone / WA | Quickstart sent | Demo date | Org approved | First paid booking | Env (mock/test/live) | Notes |
|---|---|---|---|---|---|---|---|---|---|
| — | *Example Travels* | *Jane D.* | *+91…* | ✅ | TBD | ✅ | — | mock | Format row — delete when real shortlist arrives |
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |
| 6 | | | | | | | | | |
| 7 | | | | | | | | | |
| 8 | | | | | | | | | |
| 9 | | | | | | | | | |
| 10 | | | | | | | | | |

**Target:** 5–10 shortlisted → ≥3 with one paid booking.

---

## 2. Friction log → Phase 30 backlog

Log **every** confusion or missing feature. Do not build immediately unless ship-blocking.

| Date | Agency | Friction / issue | Impact (L/M/H) | Workaround now | Phase 30 candidate? |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

**Ranking rule (after ≥2 weeks or ≥3 transacting agents):** sort by Impact × frequency → only then treat Phase 30 as “V1.5 scope”.

---

## 3. Weekly review checklist

- [ ] Admin → Failures: dead-letter jobs + failed bookings
- [ ] Home attention strip: any paid-pending / failed for pilot orgs
- [ ] Friction log: Must-fix vs Park
- [ ] All active pilots in Support WhatsApp (see `pilot-support-channel.md`)
- [ ] Update shortlist “First paid booking” column
- [ ] Chase open Sprint I/M gates if still pending

---

## 4. Demo / training calendar

| Date | Agency | Attendees | Mode (Zoom/WA) | Outcome |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

Use [`pilot-demo-script.md`](./pilot-demo-script.md) for a consistent 15–20 min walkthrough.
