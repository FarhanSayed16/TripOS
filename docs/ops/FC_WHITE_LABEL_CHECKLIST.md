# FC Phase 7 — White-label / custom domain checklist

**Owner:** Farhan (eng) · Agency admin (DNS) · Sahil (prod DNS cutover)  
**API:** `GET /api/v1/organizations/me/white-label-checklist`

## Steps

1. **Brand** — Set `brand_name` and `primary_color` on the organization.
2. **Logo** — Upload / set `logo_url`.
3. **Add domain** — `POST /organizations/domains` with the customer hostname.
4. **DNS TXT** — Publish `tripos-verify=<token>` on the domain; then `POST /organizations/domains/{id}/verify`.
   - Dev only: `{"force": true}` when `ENV != production`.
5. **TLS / edge** — Point the hostname at TripOS ingress (ops runbook; outside app).
6. **Smoke** — Open quote / search on the custom host; confirm branding loads.

## Sign-off

| Item | Owner | Date | Notes |
|---|---|---|---|
| DNS TXT verified | Agency | | |
| Ingress / TLS | Sahil | | |
| Branding smoke | Farhan | | |

When checklist `complete` is true for brand + logo + verified domain, white-label polish for FC Phase 7 is satisfied.
