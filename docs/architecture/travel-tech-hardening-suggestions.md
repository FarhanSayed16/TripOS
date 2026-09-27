# TripOS — Hardening: must-fix only (short list)

**Status:** Trimmed (2026-09-25)  
**Build from:** [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md) ← **unified phased plan with L2B**  
**Background:** Longer brainstorm archived conceptually; do not expand scope from this file.

---

## The only important extras (besides L2B cache)

| # | Issue | Integrated in readiness plan |
|---|---|---|
| 1 | **L2B / live search spam** | Phases 1, 2, 5, 7 |
| 2 | **Fare change at pay** (trust + money) | Phase 3 |
| 3 | **Pay OK / book fail** visibility | Phase 3 |
| 4 | **One org burns the feed** | Phase 4 |
| 5 | **Ticket files on ephemeral disk** | Phase 6 |
| 6 | **AI explodes supplier calls** | Phase 4 |

If it is not in this table, it is **not** required for live-inventory readiness.

---

## How we implement (pointer)

Do **not** invent a second roadmap here. Follow phases in:

**→ [`live-inventory-readiness-plan.md`](./live-inventory-readiness-plan.md)**

That document has: target architecture, file paths, env vars, acceptance tests, week calendar, and a merged checklist for L2B + these six items.

Companion detail for L2B theory only: [`look-to-book-search-cache-plan.md`](./look-to-book-search-cache-plan.md).

---

## Deferred (park — not in readiness phases)

- Compensate cancel on multi-item partial book  
- WhatsApp Cloud API  
- Orphan PNR reconcile job  
- Separate `apps/ai` service  
- Auto-settle commissions  
- NDC/LCC merge/dedupe  
- Multi-currency  

Promote into `backlog.md` only when a monthly review picks them up.
