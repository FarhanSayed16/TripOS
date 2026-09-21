# Sprint I — Live money handoff (AUDIT-009)

**Date:** 2026-09-16  
**Goal:** Unblock honest Phase 18/19 exit (one Razorpay **test** capture updating TripOS DB) and lock Phase 0 commercial answers.

This sprint is **mostly external**. Engineering can only prepare wiring + runbooks; **Nilesh / Farhan accounts / Sahil keys** close the gate.

---

## Status board

| Gate | Owner | Status | Unblocks |
|---|---|---|---|
| Commercial checklist signed | **Nilesh** | PENDING | Phase 0 DONE; live merchant assumptions |
| Razorpay **test** Key ID + Secret + Webhook secret | Farhan / Sahil | PENDING | `PAYMENTS_MODE=razorpay` |
| Webhook URL configured in Razorpay dashboard | Farhan | PENDING | Capture → DB |
| Resend API key + from-domain | **Farhan** | PENDING | Real verify/reset emails |
| Vercel project | **Farhan** | PENDING | Web deploy |
| Render API + Worker + Postgres | **Farhan** | PENDING (Blueprint ready — Sprint M) | API + outbox worker |
| Supplier sandbox pack | Sahil / Nilesh | PENDING | Phase 25 (not Sprint I blocker) |
| One test-mode capture in TripOS DB | Farhan | PENDING | Phase 19 exit |
| Pilot shortlist + demos | **Nilesh** (+ Farhan) | PENDING (pack ready — Sprint N) | Phase 29 exit |
| Phase 21 real `adapter.book` | Farhan | MOCK done; live = Phase 25 | Fulfillment |

---

## Nilesh — do this first (30–60 min)

1. Open [`COMMERCIAL_CHECKLIST.md`](./COMMERCIAL_CHECKLIST.md).
2. Replace every `[bracket]` with a real answer (or write **“Accept Farhan pilot default”**).
3. Sign the table at the bottom (name + date).
4. Send the filled file (or answers in chat) to Farhan.

**If silent / delayed:** TripOS keeps **engineering pilot defaults** (already documented in `PHASE_0_DECISIONS.md`):

| Item | Assumed until overridden |
|---|---|
| Merchant of record | Platform company Razorpay account |
| Settlement | Customer → Razorpay → Platform; agents settled offline V1 |
| Refunds | Manual only |
| Platform fee | ₹0 (`PLATFORM_FEE_PAISE=0`) |
| Supplier | Mock until Phase 25 |

These defaults are **not** a substitute for Nilesh sign-off on pilot money.

---

## Farhan — accounts & keys (same day)

Follow and fill (copy into gitignored `secrets/` — never commit values):

| Pack | Template | Local copy |
|---|---|---|
| Resend | [`credential-pack-templates/03-resend.md`](./credential-pack-templates/03-resend.md) | `secrets/03-resend.md` |
| Razorpay | [`credential-pack-templates/02-razorpay.md`](./credential-pack-templates/02-razorpay.md) | `secrets/02-razorpay.md` |
| Hosting | [`credential-pack-templates/04-hosting-accounts.md`](./credential-pack-templates/04-hosting-accounts.md) | `secrets/04-hosting-accounts.md` |

Step-by-step: [`SPRINT_I_ACCOUNT_SETUP.md`](./SPRINT_I_ACCOUNT_SETUP.md)

### Env once keys exist (`apps/api/.env`)

```env
PAYMENTS_MODE=razorpay
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
RESEND_API_KEY=re_...
FRONTEND_URL=https://your-web.vercel.app
PLATFORM_FEE_PAISE=0
ENV=development
```

### Razorpay dashboard webhook

- URL: `https://<api-host>/api/v1/webhooks/razorpay`
- Events: `payment.captured`, `payment_link.paid`
- Use the **webhook secret** as `RAZORPAY_WEBHOOK_SECRET`

### Prove Phase 19 (exit checklist)

1. Agent creates quote → ready → payment link (live short_url).
2. Pay with Razorpay **test** card.
3. Webhook hits API → `payments.status=captured`, quote `paid`, outbox `booking_confirm`.
4. Screenshot + note `gateway_payment_id` in `PHASE_0_DECISIONS.md` Sprint I section.
5. Only then mark master plan 19.3–19.4 as done.

Keep `PAYMENTS_MODE=mock` locally until steps 1–4 work once on a deployed/test API.

---

## Sahil — supplier (not blocking Sprint I money)

Fill [`credential-pack-templates/01-supplier-sandbox.md`](./credential-pack-templates/01-supplier-sandbox.md) when ready → Phase 25.

---

## Engineering shipped in Sprint I (code)

- Live Razorpay Payment Link create when `PAYMENTS_MODE=razorpay` + keys set
- Webhook accepts `payment_link.paid` as well as `payment.captured`
- `PLATFORM_FEE_PAISE` setting (default 0) applied on quote create
- Account setup runbook + this handoff

---

## Honest exit

| Claim | When true |
|---|---|
| Sprint I **packaged** | This folder + live code path exist |
| Sprint I **complete** | Nilesh signed + one test capture in DB + Resend/Vercel/Render accounts noted |
| Phase 0 **DONE** | Commercial checklist signed |
| Phase 19 **DONE** | One real test capture |
| Phase 21 start | Allowed after Sprint G/H; does not require Sprint I complete for **mock** book work |
