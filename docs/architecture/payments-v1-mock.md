# Payments V1 — mock + Razorpay test (Sprint E / I)

**Date:** 2026-09-16 (updated Sprint I)  
**Default:** `PAYMENTS_MODE=mock` until Phase 0 commercial + Razorpay **test** keys exist.

---

## Modes

| Mode | When | Behavior |
|---|---|---|
| `mock` | Local / demo | Deterministic `rzp.io/i/plink_*` URL; unsigned webhook only if not production and no secret |
| `razorpay` | Sprint I+ with keys | Live **Payment Links** via official SDK; HMAC required in production |

---

## What works

| Capability | Mock | Razorpay test |
|---|---|---|
| Create payment link + persist `payment_link_url` | Yes | Yes (`short_url`) |
| Link expiry aligned to quote `valid_until` | Ignored | `expire_by` set |
| Webhook `payment.captured` / `payment_link.paid` | Simulated | Live |
| Amount/currency verify on webhook | Yes | Yes |
| Revalidate-before-pay | Yes | Yes |
| Real test-mode money capture | No | **Exit criteria** |

---

## Env

```env
PAYMENTS_MODE=mock
# or:
# PAYMENTS_MODE=razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
FRONTEND_URL=http://localhost:3000
PLATFORM_FEE_PAISE=0
```

Webhook URL: `POST /api/v1/webhooks/razorpay`  
Handoff: `docs/phase-0/SPRINT_I_HANDOFF.md`

---

## Master plan honesty

Phases **18.3** and **19.3–19.4** stay **MOCK-COMPLETE** until one Razorpay test capture updates TripOS DB. Then flip to DONE.
