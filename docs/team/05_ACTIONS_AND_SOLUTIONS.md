# TripOS — Actions and Solutions Document

**Document type:** Issues, actions, solutions, decision log  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. How to use this doc

This is the team’s **action board narrative**: problems we already solved in engineering, problems still open, and the concrete solution path. Pair with ops runbooks under `docs/ops/`.

---

## 2. Solved in engineering (actions taken)

| Problem | Solution implemented |
|---|---|
| Sparse / inconsistent UI vs reference | Design tokens + shell + major agent/public/admin surfaces rebuilt toward NewUIReference |
| Base UI `nativeButton` console errors | Button/Drawer/Dialog/Toast composition fix; Links use `buttonVariants` (no nested button) |
| Fake money UX (80/20 fare split, random ticket #s) | Honest totals; PNR/Pending; supplier_cost only when known |
| Misleading placeholder agency hardcodes | Bind to org brand + authenticated user |
| `nav.money` missing i18n | Added EN/HI keys |
| L2B risk on every browse | Redis shopping cache + indicative labeling + live revalidate on money path |
| Pay/book race / durability | Outbox worker for booking confirm |
| Supplier cancel hard-fail | Soft-fail cancel path + audit visibility |
| Partner needs separate product | FC Phase 8 Partner API (`X-API-Key`), default **off** |
| QA needs Postman | `docs/postman/TripOS_API_Handoff/` full pack |

---

## 3. Open actions (external / next)

| # | Action | Note |
|---|---|---|
| A1 | Provide TBO sandbox credentials + path confirmation | Required for live Phase 1 E2E |
| A2 | Fill real L2B contract numbers | Provisional warn 80 / critical 120 until then |
| A3 | Commercial sign-off: primary supplier + waiver | FC Phase 0 / Phase 3 waiver |
| A4 | Hosted smoke (Render API+worker, Vercel web) | Secrets checklist in `docs/ops/` |
| A5 | Razorpay test capture → mark payments live-ready | Stay on mock until proven |
| A6 | Document vault R2/S3 in staging/prod | Prod refuses local backend |
| A7 | Second live supplier (e.g. TripJack) when delivered | Ends single-supplier waiver |
| A8 | Pilot agencies onboarding | Use agent-quickstart + demo script |

---

## 4. Incident / ops solutions (playbooks)

| Situation | Solution path | Doc |
|---|---|---|
| Payment captured, booking failed | Attention desk → Support WhatsApp → manual refund SOP | `docs/ops/PAYMENT_CAPTURED_BOOKING_FAILED.md`, `RAZORPAY_REFUND_SOP.md` |
| L2B critical | Survival soft-brakes (cache TTL, pause warm refresh, banner/Sentry) | `docs/ops/L2B_SURVIVAL_RUNBOOK.md` |
| Supplier outage | Toggle / CB + failover strategy | `docs/ops/SUPPLIER_OUTAGE_RUNBOOK.md` |
| Refund processing | Admin refunds + gateway SOP | `docs/ops/REFUND_RUNBOOK.md` |
| Backup / restore | Ops backup doc | `docs/ops/BACKUP_RESTORE.md` |

---

## 5. Honesty gaps (do not oversell)

| Gap | Correct statement to stakeholders |
|---|---|
| Default inventory | **Mock** unless TBO enabled with credentials |
| % markup | **Not implemented** — flat ₹ markup only |
| Quote “extend validity” | Master-plan item **not implemented** |
| Packages | Estimated snapshot packages — **not** live inventory packages |
| Hotels live | **Mock-gated**; TBO hotels empty |
| AI | Off by default; must not burn live L2B |
| Volt / Travclan | Evaluated; **not in current plan** |

---

## 6. Decision log (selected)

| Decision | Outcome |
|---|---|
| Product shape | B2B Agent OS (not consumer OTA) |
| V1 WhatsApp | `wa.me` first |
| Payments default | Mock until Razorpay test capture proven |
| FC Phase 3 aggregation | Multi-source tested with mock+TBO; second **live** waived |
| Partner auth V1 | API key; OAuth deferred |
| B2C storefront | Out of TripOS core; Partner API instead |
| Travclan Volt | Parked — not implementing now |

---

## 7. Recommended next sprint actions (engineering)

1. Keep Postman Happy Path green on mock.  
2. Complete hosted smoke checklist with staging secrets.  
3. With supplier credentials: TBO live smoke (search → revalidate → book cancel) in sandbox only.  
4. Close any remaining UI honesty stubs (preview-only settings clearly labeled).  
5. Pilot dry-run with one agency using agent-quickstart.  

---

*Prepared and researched by Farhan Sayed.*
