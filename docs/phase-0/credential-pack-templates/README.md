# Credential packs — how to use

## Where secrets live

| Location | In git? | Purpose |
|---|---|---|
| `docs/phase-0/credential-pack-templates/` | Yes | Empty forms — fill offline |
| `secrets/` at repo root | **No** (gitignored) | Real keys, PDFs, screenshots |

## Process

1. Copy a template into `secrets/<name>.md` (or keep in a password manager).  
2. Sahil/Nilesh fill values.  
3. Farhan integrates into env on Render/Vercel — never commit.  
4. Mark the matching row in `PHASE_0_DECISIONS.md` as received.

## Packs required for V1

1. `01-supplier-sandbox.md` — TBO or TripJack  
2. `02-razorpay.md` — test keys first  
3. `03-resend.md` — Farhan can create  
4. `04-hosting-accounts.md` — Vercel + Render  

Optional later: Upstash, WhatsApp Cloud API.
