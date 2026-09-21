# TripOS worker

The V1 DB-polling outbox worker lives in the API package (shared models/services):

```bash
cd apps/api
python worker.py
```

See [`apps/api/README.md`](../api/README.md) for local + Render Background Worker setup.

This folder is intentionally a stub so the monorepo layout matches the master plan (`apps/worker`); do not duplicate worker logic here until a Celery split is needed.
