# Phase 0 — Decisions Log (Execution)

**Phase:** 0 — Team, commercial, credentials lock  
**Started:** 2026-09-16  
**Owner:** Farhan  
**Status:** IN PROGRESS — engineering locks done; commercial + credential packs need Nilesh/Sahil fill-in

---

## 0.1 Roles & ownership — DONE

| Role | Person | Confirmed |
|---|---|---|
| Full product build (FE, BE, integrations, AI) | **Farhan** | Yes |
| Licensing, commercials, pilot agents, supply relationships | **Nilesh** | Yes |
| API credential sourcing & docs only (no app/AI code) | **Sahil** | Yes |

**Doc read-through (Farhan):** `tripos-docs-index.md` + applied reviews — done for execution start.  
**Action:** Share index + this file with Nilesh/Sahil for acknowledgment (non-blocking for Phase 1).

---

## 0.2b Flow / tech locks — DONE (Farhan)

| Decision | Value |
|---|---|
| Pax timing | Before payment link (flights full pax; hotels guest min). Not on public quote in V1 |
| Login V1 | Email + password + Resend email verify. No OTP |
| WhatsApp V1 | wa.me only |
| Quote expiry | 4h flights / 12h hotels; extend ≤24h with warning |
| Quote composition V1 | One product type per quote (flight **or** hotel only) |
| Auth cross-domain | Bearer access + Next.js BFF/proxy (default) |
| Background jobs V1 | DB-polling outbox; no Redis required |
| AI | Farhan only; Phase 35 |
| Platform fee column | Always store `platform_fee` (may be 0 in pilot) |

---

## 0.2 Commercial — PENDING Nilesh (use `COMMERCIAL_CHECKLIST.md`)

### Sprint C chase (2026-09-16)

Farhan pinged / awaiting Nilesh fill of `COMMERCIAL_CHECKLIST.md`. Until signed:

- **Engineering assumes** proposed pilot defaults below for schema + mock adapters only.
- **Do not** wire live Razorpay merchant assumptions or production supplier keys.
- **Phase 11 mock adapter is unblocked**; Phase 18 payments remain blocked on 1.1–1.3 answers.

Recommended **pilot defaults** (Farhan proposal — Nilesh must confirm or override):

| Item | Proposed pilot default | Nilesh status |
|---|---|---|
| Razorpay merchant of record | Platform (TripOS / company account) for pilot simplicity | **PENDING** |
| Who invoices customer | Platform issues payment receipt; agent issues travel invoice if required — confirm | **PENDING** |
| Settlement | Customer → Razorpay → platform; settle to agents manually offline in V1 | **PENDING** |
| Cancel/refund V1 | Manual only; “contact agent/support”; no auto-refund | **PENDING** (copy below) |
| First supplier | Prefer whichever sandbox is ready first (TBO or TripJack) | **PENDING** |
| Sandbox vs prod | Sandbox until Phase 26–28; prod keys only after Phase 28 | **PENDING** |
| Platform fee V1/pilot | **₹0** (column still stored as 0) | **PENDING** |
| Default agent markup guidance | Optional tip only — e.g. suggest 5–10% — not enforced | **PENDING** (optional) |

### Draft cancel/refund copy (V1 — edit with Nilesh)

> Cancellations and refunds are handled manually as per supplier rules. After payment, if a booking cannot be confirmed, our team will contact you. Refunds (if applicable) follow the supplier’s policy and may take several business days. For changes or cancellations after confirmation, contact your travel agent.

---

## 0.3 Credentials intake — STRUCTURE READY / VALUES PENDING

See folder: `docs/phase-0/credential-pack-templates/`  
Real secrets go in **local** `secrets/` (gitignored) — never commit keys.

| Pack | Owner to fill | Status |
|---|---|---|
| Supplier (TBO or TripJack) sandbox | Sahil / Nilesh | PENDING |
| Razorpay test keys + webhook process | Sahil / Farhan | PENDING |
| Resend API + from-email | Farhan | PENDING (Farhan can create) |
| Vercel account | Farhan | PENDING |
| Render account | Farhan | PENDING |
| Upstash | Skip for V1 | N/A |
| WhatsApp Cloud API | Not required V1 | N/A |

---

## 0.4 Exit criteria

| Gate | Status |
|---|---|
| 0.2 answers written | Partial — template + proposals; awaiting Nilesh |
| Credential pack folder exists | **Yes** — templates + gitignored `secrets/` |
| Engineering locks confirmed | **Yes** |
| Phase 0 fully DONE | **No** — until Nilesh commercial + at least supplier choice path clear |

### Parallel execution rule (agreed)

- **Phase 1–2** (monorepo + docker) may start **now** (no commercial blocker).  
- **Do not** implement live Razorpay merchant assumptions or supplier adapter until 0.2 supplier + merchant answers are filled.  
- Mock supplier + schema with `platform_fee` work regardless.

---

## Sign-off

| Person | Date | Notes |
|---|---|---|
| Farhan | 2026-09-16 | Phase 0 started; 0.1 + 0.2b locked; templates created |
| Farhan | 2026-09-16 | Sprint C: re-stated pilot defaults as engineering assumptions; commercial still PENDING Nilesh |
| Farhan | 2026-09-16 | **Sprint I:** handoff pack + live Razorpay code path shipped; awaiting Nilesh sign-off + test keys + one capture |
| Farhan | 2026-09-18 | **Sprint N:** pilot pack published (tracker, quickstart, demo script, support channel); still awaiting Nilesh agent shortlist + commercial sign-off |
| Nilesh | | |
| Sahil | | |

---

## Sprint I chase (2026-09-16)

**Packaged (engineering):**

- Handoff: `docs/phase-0/SPRINT_I_HANDOFF.md`
- Account setup: `docs/phase-0/SPRINT_I_ACCOUNT_SETUP.md`
- Code: `PAYMENTS_MODE=razorpay` → Payment Links; webhook handles `payment_link.paid`; `PLATFORM_FEE_PAISE` (default 0)

**Still PENDING (external):**

| Item | Owner |
|---|---|
| Sign `COMMERCIAL_CHECKLIST.md` | Nilesh |
| Razorpay test keys + webhook secret in `secrets/` | Farhan / Sahil |
| Resend + Vercel + Render accounts | Farhan |
| One test capture recorded below | Farhan |

**Test capture log (fill when done):**

| Date | `gateway_payment_id` | Quote id | Env (test) |
|---|---|---|---|
| | | | |

**Do not mark Phase 0 or Phase 19 DONE until the capture row is filled and Nilesh has signed.**

---

## Sprint N chase (2026-09-18)

**Packaged (engineering / ops):**

- Tracker: `docs/pilot-onboarding-tracker.md`
- Quickstart: `docs/agent-quickstart.md`
- Demo script: `docs/pilot-demo-script.md`
- Support channel: `docs/pilot-support-channel.md`
- Failures / refunds: `docs/ops/PAYMENT_CAPTURED_BOOKING_FAILED.md`, `RAZORPAY_REFUND_SOP.md`

**Still PENDING (external):**

| Item | Owner |
|---|---|
| Fill agent shortlist (5–10) | **Nilesh** |
| Sign `COMMERCIAL_CHECKLIST.md` | **Nilesh** |
| Create Pilot Support WhatsApp + invite | Farhan / Nilesh |
| Schedule first 3 demos | Nilesh + Farhan |
| Hosted smoke + test capture | Farhan (Sprint I/M leftovers) |
| ≥3 real paid bookings | Agents + live money |

**Sprint N is packaged, not complete.** Phase 29 exit stays open until real agents transact.
