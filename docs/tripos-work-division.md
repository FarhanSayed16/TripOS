# TripOS — Work Division (Finalized)

### Companion to `tripos-plan.md`, `tripos-modules-and-flow.md`, and `tripos-master-plan.md`

---

## 1. The Split, in One Line (FINAL)

**Farhan owns the entire product build:** frontend, backend, inventory/adapters, payments, wa.me messaging, **and the AI Copilot (V2)** — including prompts, LLM wiring, and `apps/ai`.  

**Nilesh + Sahil provide access and domain input only:** live/sandbox **API credentials, commercial terms, and documentation**. They do **not** build the AI engine or application code.

**Farhan integrates** every API into the product.

---

## 2. Farhan — Scope (everything buildable)

| Area | Owns |
|---|---|
| Frontend (Vercel) | Full Next.js: marketing, auth, Agent OS, Admin OS, public quote |
| Backend (Render) | FastAPI modular monolith: all V1–V3 modules |
| AI Copilot (V2) | `apps/ai` + AI gateway in main API + AI UI; LLM provider account/keys for the product |
| Supplier adapters | All integration code (TBO/TripJack/etc.) |
| Payments / Resend / wa.me | All integration code |
| White-label, hierarchy, wallet, packages, follow-ups | All product code when those phases open |
| Deploy / CI / schema | Full ownership |

---

## 3. Sahil Shah — Scope (FINAL: credentials & docs only)

**Does:**
- Source and document supplier API access (TBO/TripJack, later others)
- Source and document Razorpay (and PayU if needed) test/live credentials
- Source WhatsApp **Cloud API** later if/when product upgrades from wa.me
- Help with Resend/Upstash account access if useful
- Hand Farhan a **credential pack** per partner: base URL, auth method, sandbox vs prod, rate limits, sample request notes, refund/cancel quirks

**Does not:**
- Write TripOS application code
- Build or own the AI Copilot
- Call product inventing of architecture
- Train models for TripOS

---

## 4. Nilesh — Scope (business + supply)

- Licensing / compliance (IATA/TAAI/FAAT/Aviation as applicable)
- Supplier commercial relationship and which supplier goes live first
- Margin/settlement judgment; who is merchant of record / invoicing party
- Pilot agent network (first 5–10 agents)
- Domain feedback on real agent workflows

**Does not:** write application code or AI.

---

## 5. API handoff pattern (Nilesh/Sahil → Farhan)

```text
Nilesh/Sahil secure access + docs
        │
        ▼
Credential pack delivered to Farhan
        │
        ▼
Farhan implements adapter / Razorpay / etc. in TripOS
```

Same pattern for every future external API (path to hundreds of suppliers): **they source, Farhan builds the adapter**.

---

## 6. AI (FINAL)

| Item | Owner |
|---|---|
| AI Copilot service & prompts | **Farhan** |
| LLM vendor key / billing for product | **Farhan** (company account ok) |
| Inventory search called by AI flow | **Farhan** (AI never calls suppliers itself) |
| Optional later fine-tuning | **Farhan** only if ever approved — still not required for V2 |

Contract shapes for parse-intent / format-quote-draft remain useful as **Farhan’s own internal API design** — see `tripos-ai-spec.md` (formerly Sahil handoff; now Farhan-owned spec).

---

## 7. Module Ownership Table (FINAL)

| Module | Phase | Owner |
|---|---|---|
| Auth, Orgs, CRM, Quotes, Bookings, Payments, Messaging (wa.me), Admin, Audit | V1 | **Farhan** |
| Inventory + adapters | V1 | **Farhan** (creds: Sahil/Nilesh) |
| AI Copilot | V2 | **Farhan** |
| Packages, Wallet, Follow-ups | V2 | **Farhan** |
| White-label, Distributors, multi-supplier strategies | V3 | **Farhan** |
| Supplier / Razorpay / later WhatsApp Cloud **access** | as needed | **Sahil/Nilesh source → Farhan integrates** |

---

## 8. Immediate Next Steps

1. Sahil/Nilesh: supplier #1 + Razorpay credential packs (before inventory live weeks)  
2. Farhan: execute `tripos-master-plan.md` from Phase 0/1  
3. Farhan: AI only when Phase 35 (after V1 exit gate) — same person, later phase  
4. Equity/role conversation still accounts for Sahil/Nilesh non-code contributions  
