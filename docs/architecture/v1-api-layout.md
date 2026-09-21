# V1 API layout — flat package acceptance (FIX-20)

**Date:** 2026-09-16  
**Decision:** **A — Accept flat layout for V1**

---

## Context

`tripos-backend-plan.md` describes `modules/<name>/` (router, schemas, service, repository).  
Implemented code uses:

```
apps/api/app/
  api/          # routers (auth, customers, organizations, health)
  schemas/
  models/
  services/
  utils/
  core/
  db/
```

## Decision

Keep the **flat layout through V1** (through payments/bookings). Do **not** mass-refactor to `modules/*` before Phase 11+.

## Rules (enforce by convention)

1. One router file (or package) per domain under `app/api/`.
2. Business logic that grows beyond ~thin handlers moves to `app/services/<domain>.py`.
3. No supplier HTTP from routers — inventory adapters own vendor I/O.
4. When a domain exceeds ~3 files of logic, **then** extract `app/modules/<name>/` for that domain only (incremental, not big-bang).

## Doc amendment

Backend plan `modules/*` remains the **target shape for large domains**; V1 scaffolding is intentionally flat for speed. This ADR supersedes any implication that V1 must already use `modules/*`.
