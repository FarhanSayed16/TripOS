# TripOS — Documentation Index & How to Use the Master Plan

### Companion to `tripos-master-plan.md`

**Status:** Source-of-truth map for all planning docs  
**Execution file:** Always drive day-to-day build from **`tripos-master-plan.md`** (phases + checklists).  
**This file:** Where every other doc fits, what is locked, and how the team uses the master plan without getting lost.

---

## 1. The two execution documents (created for project delivery)

| # | File | Role |
|---|---|---|
| **1** | [`tripos-master-plan.md`](./tripos-master-plan.md) | **Final checkpoint / checklist.** 40 phases, sub-phases, deliverables. Use this to execute the whole project without missing items. |
| **2** | [`tripos-docs-index.md`](./tripos-docs-index.md) (this file) | **Map of all docs**, locked decisions, reading order, ownership. Use this when you need detail behind a master-plan checkbox. |

All earlier docs remain valid **detail references**. If anything conflicts, **Master Plan + this Index win** for execution order; detail docs win for *how* a module is shaped.

---

## 2. Full document library

| Document | What it contains | When to open it |
|---|---|---|
| `tripos-plan.md` | Vision, ICP, business model, GTM, original V1–V3 product story | Aligning “why” with Nilesh / investors |
| `tripos-modules-and-flow.md` | Module list, dependencies, end-to-end flows, rough API surface | Understanding product modules & flows |
| `tripos-work-division.md` | **FINAL:** Farhan builds all code/AI; Sahil/Nilesh supply API access only | Ownership |
| `tripos-ai-spec.md` | AI Copilot internal contract (Farhan-owned); replaces old Sahil handoff | Building Phase 35 AI |
| `tripos-enhancements.md` | Ideas backlog, V1 small / V1.5 / park list | Prioritizing extras without scope creep |
| `tripos-implementation-plan.md` | Stack, adapter platform for many APIs, phased delivery narrative | Architecture & multi-supplier mindset |
| `tripos-backend-plan.md` | Backend folders, modules, services, jobs — no code | Building API structure |
| `tripos-frontend-plan.md` | Pages, nav, theme, motion, FE structure — no code | Building UI structure |
| **`tripos-master-plan.md`** | **40-phase execution checklist** | **Daily / weekly build progress** |
| `tripos_plan_review.md` | Cross-doc review (18 issues + enhancements) — **RESOLVED into plans** | Historical; do not re-apply blindly |
| **`phase-0/`** | **Phase 0 execution:** decisions, commercial, credentials, **`SUPPLIER_L2B_CONTRACT.md`** | **Current execution** |
| **`phase-0-10-audit-fixes.md`** | **Audit of Phases 0–10:** gaps, bugs, prioritized fixes | **Fix before Phase 11** |
| **`phase-11-20-audit-fixes.md`** | **Audit of Phases 11–20:** adapter→pay→worker gaps, P0 bugs | **Fix before claiming Phase 20 / starting Phase 21** |
| **`phase-21-30-audit-fixes.md`** | **Audit of Phases 21–30** + Sprints J–N | **Current 21–30 source of truth** |
| **`phase-31-40-audit-fixes.md`** | **Audit of Phases 31–40** — V2/V3 gaps, security, GO/NO-GO | **Do not claim Phase 40 done** |
| `architecture/phase-4-schema-decisions.md` | JWT verify, phone unique, deferred tables | Schema honesty / migrations |
| `architecture/v1-api-layout.md` | Flat `app/api` accepted for V1 (vs `modules/*`) | Backend structure decisions |
| `architecture/payments-v1-mock.md` | Mock payments mode until live Razorpay | Phase 18–19 honesty |
| `architecture/inventory-v1-mock.md` | Mock-only suppliers / TBO gate | Phase 25 honesty |
| **`architecture/live-inventory-readiness-plan.md`** | **Unified phases: L2B cache + must-fix hardening** | **Build this before live supplier scale** |
| **`architecture/live-inventory-phases-0-7-explained.md`** | **Conceptual narrative: why/how Phases 0–7 help** | Product / ops / commercial readout |
| `architecture/look-to-book-search-cache-plan.md` | L2B theory + cache design detail | Background for readiness plan |
| `architecture/travel-tech-hardening-suggestions.md` | Short must-fix list (points to readiness plan) | Scope control |
| **`pilot-onboarding-tracker.md`** | Phase 29 shortlist + friction log | **Sprint N — Nilesh fills agents** |
| **`sprint-p-status.md`** | Sprint P V1 leftover board | Hosted/commercial gates |
| **`sprint-qrst-status.md`** | Sprints Q–T engineering close | Prototype honesty + code exits |
| **`packages-v1-honesty.md`** | Packages = price snapshots | Phase 32 |
| **`wallet-commission-formula.md`** | Ledger / hierarchy BPS | Phase 33/38 |
| **`multi-supplier-honesty.md`** | Failover + simulated TBO | Phase 36 |
| **`monthly-review-2026-09.md`** | First Phase 40 monthly review | Cadence |
| **`agent-quickstart.md`** | Agent 1-pager | Pilot training |
| **`pilot-demo-script.md`** | 15–20 min demo outline | Live demos |
| **`pilot-support-channel.md`** | WhatsApp support norms | Pilot ops |
| **`ops/`** | Render/Vercel, smoke, refunds, pay-failed, Phase 28, **`L2B_SURVIVAL_RUNBOOK.md`** | Hosted + reliability + L2B |

| `failure-taxonomy.md` | Booking failure codes ↔ UI copy | Support |
| `e2e-runs.md` | How to run E2E + green-run log | CI / local Postgres |

---

## 3. Locked decisions (do not re-debate during V1)

| Area | Decision |
|---|---|
| Product | B2B Travel **Agent OS** (not consumer OTA) |
| V1 loop | Search → Quote → **wa.me** → Pay → Book → CRM |
| Frontend | Next.js + TypeScript on **Vercel** |
| Backend | FastAPI modular monolith on **Render** |
| DB | PostgreSQL |
| Redis | **Upstash** when needed |
| Email verify | **Resend** |
| WhatsApp V1 | **wa.me** links (Cloud API later) |
| Payments | Razorpay (primary) |
| Login V1 | **Email + password + Resend** (no OTP) |
| Pax timing | **Before payment link** (agent fills; not public page in V1) |
| Auth cross-domain | **BFF/proxy + Bearer** (default) |
| Quote expiry default | **4h flights / 12h hotels** (extend ≤24h with warning) |
| V1 quote composition | **One product type per quote** (flight-only or hotel-only) |
| V1 background jobs | **DB-polling outbox** (Upstash/Celery optional later) |
| Inventory | Adapter platform; V1 = mock + one real supplier |
| AI | V2; **Farhan only**; **no training required**; Sahil/Nilesh = APIs/creds only (not AI) |
| AI prices | Never invent; only format real search |
| White-label / hierarchy / multi-supplier merge | **V3** (schema hooks in V1 only) |
| Theme | Coastal ink desk (ink + teal + paper) — see frontend plan |
| Success metric | Monthly Active **Transacting** Agents |
| Plan review | `tripos_plan_review.md` — **APPLIED** 2026-09-16 |

---

## 4. Recommended reading order (new contributor)

1. This index (5 min)  
2. `tripos-plan.md` §§1–4 (product)  
3. `tripos-master-plan.md` Phase overview table  
4. `tripos-backend-plan.md` + `tripos-frontend-plan.md` for the phase you are on  
5. Detail docs only as needed  

---

## 5. How to use the Master Plan as a checklist

1. Work **one phase at a time** (or one sub-phase).  
2. Check every `- [ ]` item before marking the phase **DONE**.  
3. Do not start V2 phases until **Phase 31 (V1 Exit Gate)** is complete.  
4. If an enhancement is needed mid-flight, add it under the correct phase’s “Optional” or park it in enhancements — do not silently expand V1.  
5. After each phase: note date, owner, blockers at the bottom of that phase in the master plan (or in your tracker).  

---

## 6. Ownership default

| Track | Default owner |
|---|---|
| Backend, frontend, integrations, deploy | **Farhan** |
| Supplier/Razorpay credential packs | **Sahil / Nilesh** (source) → **Farhan** (integrate) |
| AI Copilot service | **Farhan only** — see `tripos-ai-spec.md` |
| Licensing, agent pilot network, commercials | **Nilesh** |

---

## 7. Version map vs master phases

| Product version | Master plan phases (approx.) |
|---|---|
| Foundations + V1 core | Phases 0–28 |
| Pilot + V1.5 + V1 exit | Phases 29–31 |
| V2 | Phases 32–35 |
| V3 + scale | Phases 36–40 |

---

**Next step:** Open [`tripos-master-plan.md`](./tripos-master-plan.md) and start at **Phase 0**.
