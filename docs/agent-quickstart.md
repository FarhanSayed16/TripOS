# TripOS — Agent quick start

**Audience:** Pilot agencies  
**Flow:** Search → Quote → Send (WhatsApp) → Pay → Booking

Use this as the 1-pager. For a live call, follow [`pilot-demo-script.md`](./pilot-demo-script.md).

---

## Before you start

1. You have a TripOS login and your agency is **approved** (status active).
2. Open the app URL Farhan sent (production or staging).
3. During early pilot, inventory may be **mock** (practice money flow). Farhan will tell you when Razorpay test/live is on.

---

## 1. Search

1. Log in → go to **Search**.
2. Enter origin, destination, date, passengers.
3. Pick an offer. You’ll see supplier cost vs what you’ll charge after markup.

## 2. Quote

1. Create a **Customer** (name + WhatsApp phone) if needed.
2. **Create quote** from the offer; set your **markup**.
3. Add **passenger names** (required before Ready / Pay).
4. Mark quote **Ready**.

## 3. Send on WhatsApp

1. Open the quote → **WhatsApp preview** / **Send**.
2. Customer gets a branded link (`/q/…`). They never see your net cost.

## 4. Payment & booking

1. Customer pays on the public page (Razorpay when live; mock/offline in training).
2. TripOS queues automatic supplier booking in the background.
3. Watch **Home** (attention items) and **Bookings**:
   - **Confirmed** → PNR shown on the quote
   - **Failed / Needs support** → open the quote; message Support WhatsApp (do **not** invent a refund in the app — refunds are manual)

**Booking detail** = the **quote page** (there is no separate booking-only screen).

## 5. If something goes wrong

| Symptom | What to do |
|---|---|
| Can’t mark Ready | Add passengers first |
| Pay link blocked (fare / sold out) | Re-search and new quote |
| Customer paid, no PNR | Home → failed/pending item → quote → ping Support |
| Wrong agency data | Never share logins across agencies |

Ops detail for Farhan: [`ops/PAYMENT_CAPTURED_BOOKING_FAILED.md`](./ops/PAYMENT_CAPTURED_BOOKING_FAILED.md).

---

## Need help?

Message the **TripOS Pilot Support** WhatsApp group (invite from Farhan/Nilesh).  
Include: agency name, quote id (first 8 characters), and a screenshot.
