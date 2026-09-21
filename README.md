# TripOS

TripOS is a B2B travel agent operating system designed to enable agents to search for flights and hotels, build margin quotes, share them via WhatsApp, collect payments, and automatically confirm bookings.

## Monorepo Structure

- `apps/web`: Next.js frontend application (App Router, Tailwind CSS, TypeScript).
- `apps/api`: FastAPI backend service.
- `apps/worker`: Celery worker for background jobs.
- `apps/ai`: AI copilot service.
- `adapters`: Supplier integration adapters (e.g., TBO, TripJack).
- `docs`: Planning and architecture documentation.

## Engineering Standards

- **Python Version:** 3.12+
- **Node.js Version:** LTS (20+)
- **Formatting and Linting:**
  - Python: `ruff` and `black`
  - Next.js: `eslint` and `prettier`
- **Commit Convention:** Keep commit messages short and focused on *why* the change is made.
- **Branch Strategy:** Main branch for production, feature branches for active development.
- **Secrets Policy:** Never commit secrets to the repository.

## Architecture Decisions
- **Cross-Domain Auth (Vercel <-> Render):** We use a Next.js BFF (Backend-For-Frontend) proxy pattern. The frontend calls `/api/*` on its same origin, which the Next.js server proxies to the FastAPI backend with `Authorization: Bearer` headers. Refresh tokens will be stored as HttpOnly cookies on the Next.js side if needed.

See the [Documentation Index](./docs/tripos-docs-index.md) for more details.

## Local Development Runbook

1. **Start Infrastructure (Postgres & Redis):**
   ```bash
   docker compose up -d
   ```

2. **Run the Backend API:**
   ```bash
   cd apps/api
   # Setup virtual environment and dependencies (using venv/uv/poetry)
   # Placeholder command for now:
   uvicorn main:app --reload --port 8000
   ```

3. **Run the Web Frontend:**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
