# TripOS secrets (DO NOT COMMIT)

Put real credential packs here (copied from `docs/phase-0/credential-pack-templates/`).

This folder is gitignored. If you accidentally commit a secret, rotate it immediately.

## Hosting accounts (Sprint M)

After first Render + Vercel deploy:

```text
copy docs\phase-0\credential-pack-templates\04-hosting-accounts.md secrets\04-hosting-accounts.md
```

Fill production URLs, Dashboard links, and who owns each account. Never commit that file.
