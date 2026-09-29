# Partner API — what TripOS is **not**

**Audience:** B2C brand / external partner engineering + TripOS product  
**Phase:** FC Phase 8

TripOS is a **B2B agent OS**. The Partner API lets a **separate** B2C (or partner) product consume inventory/booking capabilities without sharing a codebase or agent JWTs.

## Belongs in the B2C product (not TripOS)

| Capability | Why not here |
|---|---|
| Consumer storefront / catalog SEO | Marketing site for travelers |
| Reviews, ratings, UGC | Consumer trust layer |
| Social / referral consumer loops | Growth product |
| Traveler accounts & loyalty UI | B2C identity |
| Content CMS for destinations | Separate brand |

## Belongs in TripOS (via Partner API)

- Search / revalidate / quote / pay-link / booking status / cancel
- Org-scoped tenancy, L2B brakes, signed webhooks
- Admin CRUD for partner apps + key rotation

## Hard rule

**Do not merge B2B and B2C codebases.** Integration contract = Partner API + webhooks only.
