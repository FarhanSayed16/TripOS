# Gap Analysis — Team Input vs TripOS Built Today

**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-08  
**Sources:**
- `docs/teaminputs/B2B_Travel_Platform_India_Findings_Recommendations.md`
- `docs/teaminputs/workflow.md` (**empty** — original workflow attachment not present)
- Live codebase (`apps/api`, `apps/web`) + existing `docs/team/`

---

## 0. Important framing (read first)

| Question | Answer |
|---|---|
| Is the team input a rebuild of TripOS architecture? | **No.** It is an **India ops / compliance / controls** review of an assumed B2B travel workflow. |
| Does TripOS already match the core product journey? | **Yes, largely** — Search → Quote → Share → Pay → Book → CRM already exists (mock inventory / mock pay by default). |
| What is missing? | Mostly **production-India controls** (KYC, GST/invoice, consent, MFA, stronger refunds, etc.) + finishing **live** supplier/payment gates. |
| `workflow.md` | Empty. We cannot match line-by-line to the “attached workflow” until that file is provided. Analysis uses the Findings doc + code. |

**Do not treat the Findings ownership/RACI tables as a product rebuild checklist.** They are governance roles for launch readiness. Below is the **engineering / product work** that maps to those controls.

---

## 1. Where we stand (product core)

| Capability | Status today | Notes |
|---|---|---|
| Agency signup + org approve/reject | **Partial** | `pending_approval` → admin activate; **no KYC docs / GSTIN / verification checklist** |
| Multi-org agents + roles | **Built** | JWT, org membership, platform admin |
| CRM customers | **Built** | No privacy/consent capture |
| Flight search | **Partial** | `mock_supplier` default; TBO sim/live gated |
| Hotels | **Partial** | Mock UX; TBO hotels empty |
| Quote + flat ₹ markup + public page | **Built** | `% markup` not built |
| WhatsApp share | **Built** | `wa.me` only — no Cloud API |
| Fare rules display | **Partial** | API + quote UI exist; public pay path disclosure may still need hardening |
| Payments | **Partial** | Default **mock**; Razorpay path exists behind flag |
| Outbox booking → PNR | **Built** | Worker path |
| Cancel | **Partial** | Soft-fail cancel + refunds queue |
| Change / reissue | **Mock-only** | Records fee; no live supplier reissue |
| Wallet | **Built** | Commission ledger — **not** prepaid deposit credit |
| Packages | **Partial** | Snapshot estimates |
| Partner API | **Partial** | Code on; flag **off** |
| L2B cache / survival | **Built** | Flags often off in local |
| Audit events | **Partial** | `audit_events` + admin export; not full immutable “old/new” compliance pack |
| Invoice PDF / GST | **Missing** | UI says “Invoice PDF (coming soon)” |
| Bus / train / visa / insurance | **Missing** | Flight + hotel only |
| MFA | **Missing** | Email/password only |

---

## 2. Findings gaps → TripOS map

Legend: **Have** = usable now · **Harden** = exists but incomplete for India launch · **Build** = not in product · **Ops/Legal** = process + counsel, not only code

| Findings gap | Priority (doc) | TripOS today | What to do |
|---|---|---|---|
| Agency KYC / KYB | P0 | Approve toggle only | **Build** KYC fields, document upload, verification status, block booking until verified |
| GST & tax / invoices | P0 | No GSTIN model; invoice PDF missing | **Build** GSTIN on org, tax breakup, invoice numbering, credit/debit notes (Finance rules with counsel) |
| Customer consent & privacy | P0 | CRM stores data freely | **Build** notice + consent flags on customer create; retention/export/delete policy + APIs |
| Payment compliance | P0 | Mock default; Razorpay + webhook exist | **Harden** live Razorpay, settlement docs, chargeback SOP; keep tokens out of app |
| Refund & cancellation governance | P0 | Refund statuses + admin queue + SOPs | **Harden** maker-checker approval, reason codes, customer notify, supplier-ref linkage |
| Supplier fare/terms before book | P0 | Fare-rules service + agent UI | **Harden** mandatory display on public pay + ready-to-pay; log acceptance |
| Audit trail | P0 | `audit_events` written on key paths | **Harden** old/new values, privileged-action coverage, retention |
| Access / security (MFA, etc.) | P0 | JWT, token version, secrets patterns | **Build** MFA for admin/privileged; password policy; access-review export |
| Grievance / dispute | P1 | Attention desk + support WhatsApp SOPs | **Build** ticket entity OR integrate support tool; SLA fields |
| Contract / terms version acceptance | P0 | Not in product | **Build** versioned terms + acceptance log (who/when/version) |
| Communication compliance | P1 | Resend transactional; wa.me | **Harden** transactional vs promo; preference flags |
| Business continuity | P1 | Ops runbooks exist | **Ops** — backup/DR drills, incident template already in `docs/ops/` |
| Fraud / risk controls | P0/P1 | L2B meters; little booking fraud logic | **Build** velocity / duplicate / high-risk agency flags (start simple) |
| Operational reconciliation | P0/P1 | Wallet + payments lists | **Build** daily recon report (supplier cost vs capture vs markup) |
| Data ownership / retention | P0 | Soft-delete patterns | **Build** retention schedule + delete/anonymise jobs; **Ops/Legal** policy text |

---

## 3. What you do **not** need to rebuild

These are already the product spine. Do **not** restart architecture for the Findings doc:

1. Modular monolith (Next.js + FastAPI + worker + Postgres + Redis)  
2. Quote / public token / wa.me loop  
3. Adapter interface (`mock` + `tbo`)  
4. Outbox booking confirm  
5. Org multi-tenancy + partner API scaffold  
6. Existing ops runbooks for pay-failed / refund / L2B / outage  

**Optional later (not demanded by Findings):** TripJack, Cloud WhatsApp, % markup, prepaid agent credit, bus/train/visa, Travclan Volt.

---

## 4. Exact work plan (what to implement)

### Track A — Finish commercial spine (already planned; still blocking “real” demos)

| ID | Work | Outcome |
|---|---|---|
| A1 | TBO sandbox credentials + live smoke | Live search → revalidate → book/cancel in sandbox |
| A2 | Razorpay test mode end-to-end | Real capture + webhook → worker book |
| A3 | Hosted smoke (Vercel + Render + managed DB) | Staging URL for pilots |
| A4 | Document vault S3/R2 | Prod-safe tickets/PDFs |
| A5 | Public + agent fare-rule gate before pay | Disclosure control from Findings |

### Track B — India production controls (from Findings P0)

| ID | Work | Outcome |
|---|---|---|
| B1 | Agency KYC/KYB workflow | Docs + status; no booking until `verified` (separate from mere `active`) |
| B2 | Org GSTIN + invoice generation | Tax breakup + numbered invoice PDF; cancel/credit note path |
| B3 | Terms / privacy version acceptance | Signup + booking accept logs |
| B4 | Customer consent on CRM create | Notice shown + stored consent timestamp |
| B5 | MFA for platform admin (+ org admin) | Privileged access control |
| B6 | Refund maker-checker | Two-step approve before gateway refund / mark settled |
| B7 | Audit harden | Diff fields on markup override, refund, role change, config |
| B8 | Grievance tickets (minimal) | Create/list/SLA/close linked to booking |

### Track C — Early production (Findings P1)

| ID | Work | Outcome |
|---|---|---|
| C1 | Daily reconciliation report | Capture vs supplier vs markup exceptions |
| C2 | Simple fraud rules | Velocity, duplicate pax/route, manual hold |
| C3 | Retention/deletion jobs | Per policy schedule |
| C4 | Backup/DR test evidence | Ops checklist signed off |
| C5 | Access review export | Who has admin / partner keys |

### Track D — Explicitly out of scope until decided

- Full RACI product embedding as named business roles  
- AI grievance / predictive fraud (Findings P2)  
- Second live supplier, Cloud WhatsApp, prepaid wallet, non-air verticals  

---

## 5. Suggested sequence (next 4–6 engineering slices)

```text
1. Track A (live TBO + Razorpay + hosted)     → prove money path for real
2. B5 MFA + B7 audit harden                   → security baseline
3. B3 terms + B4 consent                      → privacy baseline
4. B1 KYC gate                                → agency trust baseline
5. A5 + B6 fare disclosure + refund checker   → booking/refund governance
6. B2 GST/invoice                             → finance launch blocker
7. B8 grievance + Track C                     → early production
```

Legal/tax counsel still validates B2/B3 wording and GST treatment — Findings §9.

---

## 6. Matching score (honest)

| Layer | Match to Findings “workflow” intent |
|---|---|
| Core B2B journey (search–book–CRM) | **~80% built** (mock/live honesty applies) |
| India compliance controls | **~15–25% built** (audit/refund/org approve seeds only) |
| Ops runbooks / continuity docs | **~50%** (docs exist; drills/automation incomplete) |
| Finance GST/invoice | **~5%** (placeholders) |

**Bottom line:** TripOS is **not** off-plan architecturally. The team input says: **keep the product, add India launch controls**, and finish **live pay + live inventory**. The empty `workflow.md` should be filled or attached if you need a stricter line-by-line match to the original process diagram.

---

*Prepared and researched by Farhan Sayed.*
