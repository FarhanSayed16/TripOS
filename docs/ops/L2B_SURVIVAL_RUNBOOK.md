# L2B survival soft-brakes (Phase 7)

**Owner:** Farhan · **Related:** `architecture/live-inventory-readiness-plan.md` Phase 7 · `PHASE_39_CHECKLIST.md`

## What it is

When **platform** rolling L2B hits `critical` (`L2B_CRITICAL_RATIO`, default 120), TripOS auto soft-brakes:

| Action | Default |
|---|---|
| Widen shopping-cache TTL | × `L2B_SURVIVAL_TTL_MULTIPLIER` (2), capped at `L2B_SURVIVAL_TTL_CAP_SECONDS` (900) |
| Pause warm-band background refresh | Keep hot-band only (`SEARCH_CACHE_HOT_TOP_N`) |
| Admin banner | Red bar across `/admin/*` while active |
| Sentry | `capture_message` (5 min cooldown) when DSN set |

Looks = live `search` + `revalidate` from `supplier_usage_daily`. Cache hits are not looks.

## Flags

| Env | Default | Notes |
|---|---|---|
| `L2B_SURVIVAL_ENABLED` | `true` | Master kill for auto brakes |
| `L2B_SURVIVAL_TTL_MULTIPLIER` | `2` | Applied only when status=critical |
| `L2B_SURVIVAL_TTL_CAP_SECONDS` | `900` | Hard ceiling on widened TTL |
| `L2B_SURVIVAL_PAUSE_WARM_REFRESH` | `true` | Skip warm routes in Phase 5 refresher |
| `L2B_WARN_RATIO` / `L2B_CRITICAL_RATIO` | 80 / 120 | Provisional until Sahil contract |

API: `GET /admin/l2b/survival` · also embedded in `GET /admin/analytics` as `l2b_survival`.

## Ops playbook

### 1. Confirm critical

1. Admin banner visible, or Analytics “Platform L2B (7d)” red.
2. `GET /admin/l2b` → `status: critical`, check `survival.active`.
3. Sentry issue / log: `l2b_survival_critical` / `l2b_survival_active`.

### 2. Immediate (auto already on)

- Do **not** disable shopping cache (`SEARCH_CACHE_ENABLED`) unless Redis is broken.
- To fully stop background live calls: set `SEARCH_CACHE_REFRESH_ENABLED=false` on the **worker** and redeploy/restart.
- Review `GET /admin/l2b/orgs` for offender orgs (Phase 4 throttle may already block them).

### 3. Manual overrides

| Goal | Action |
|---|---|
| Disable survival brakes only | `L2B_SURVIVAL_ENABLED=false` (API + worker) |
| Keep survival but allow warm refresh | `L2B_SURVIVAL_PAUSE_WARM_REFRESH=false` |
| Stronger TTL | Raise multiplier or cap carefully (staler fares) |
| Kill all refresh | `SEARCH_CACHE_REFRESH_ENABLED=false` |

### 4. Clear critical

Increase confirmed bookings and/or cut looks (cache hit rate, org throttle, pause AI live). Survival turns off when 7d status ≠ `critical` (in-process cache refreshes ~45s).

### 5. Staging simulation

1. Seed / fake `supplier_usage_daily` so looks/confirmed ≥ critical, **or** temporarily lower `L2B_CRITICAL_RATIO`.
2. Hit search (cache miss) → logs show widened TTL via `effective_cache_ttl`.
3. Run cache refresh job → `skipped_warm` > 0, `pause_warm_refresh: true`.
4. Admin banner appears within ~1 min (poll).
5. Restore ratio / env.

## Related runbooks

- Pause refresher only: `PHASE_39_CHECKLIST.md` → Search cache
- Org throttle: Phase 4 / Analytics org L2B table
- Supplier outage: `SUPPLIER_OUTAGE_RUNBOOK.md`
