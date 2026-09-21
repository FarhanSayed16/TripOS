# Sprint I — Account setup runbook (Farhan)

Do these in order. Put secrets only under gitignored `secrets/`.

---

## 1. Resend (email)

1. Create account at [resend.com](https://resend.com).
2. Create API key → paste into `secrets/03-resend.md` and `apps/api/.env` as `RESEND_API_KEY`.
3. Add + verify sending domain (or use `onboarding@resend.dev` for early tests only).
4. Set `FRONTEND_URL` to the web origin used in verify/reset links.
5. Smoke: signup → check Resend dashboard / inbox for verify mail (logs must show redacted token only).

---

## 2. Razorpay (test mode)

1. Confirm merchant-of-record with Nilesh (or accept pilot default: **platform account**).
2. Razorpay Dashboard → **Test mode** → API Keys → generate Key ID + Secret.
3. Settings → Webhooks → add:
   - URL: `https://<api-host>/api/v1/webhooks/razorpay`
   - Secret: generate → `RAZORPAY_WEBHOOK_SECRET`
   - Events: `payment.captured`, `payment_link.paid`
4. Fill `secrets/02-razorpay.md`.
5. Set env:

```env
PAYMENTS_MODE=razorpay
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

6. Install API dep if needed: `pip install razorpay` (listed in `apps/api/pyproject.toml`).
7. Create payment link from agent UI → open short URL → pay with [Razorpay test cards](https://razorpay.com/docs/payments/payments/test-card-details/).
8. Confirm DB: `payments.status = captured`, quote `paid`.

---

## 3. Vercel (web)

1. Import `apps/web` (or monorepo root with correct root directory).
2. Env: `NEXT_PUBLIC_API_URL`, `API_ORIGIN` pointing at Render API.
3. Note project URL in `secrets/04-hosting-accounts.md`.
4. Update API `FRONTEND_URL` + CORS allowlist to the Vercel URL.

---

## 4. Render (API + worker + Postgres)

1. Create Postgres → copy `DATABASE_URL` (`postgresql+psycopg://...`).
2. Web service: root `apps/api`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Background Worker: root `apps/api`, start `python worker.py`, **same** `DATABASE_URL`.
4. Env: `JWT_SECRET` (strong), `ENV=production` only when ready, payments + Resend keys, `FRONTEND_URL`.
5. Run `alembic upgrade head` (release command or one-off shell).
6. Point Razorpay webhook at the public API URL.

---

## 5. Sign-off note

When done, append to `PHASE_0_DECISIONS.md` → Sprint I section:

- Resend: yes/no + from-domain  
- Vercel URL  
- Render API URL  
- Razorpay test capture: payment id / date  
- Nilesh commercial: received / still pending  
