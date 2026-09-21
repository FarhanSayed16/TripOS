# Vercel Operational Runbook

This document describes how to deploy, rollback, and manage the TripOS Frontend (Web) on Vercel.

## 1. Initial Deployment

1. Create an account on [Vercel](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Import the TripOS GitHub/GitLab repository.
4. **Configuration Details:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `apps/web` (Important! Do not leave this as the repository root)
   - **Build Command:** `next build` (default)
   - **Output Directory:** `.next` (default)
5. **Environment Variables:**
   - `NEXT_PUBLIC_API_URL` — Render API origin + `/api/v1` (e.g. `https://tripos-api.onrender.com/api/v1`)
   - `NEXT_PUBLIC_SENTRY_DSN` or `SENTRY_DSN` — frontend error reporting
   - `SENTRY_ORG` / `SENTRY_PROJECT` — optional source-map upload
6. Click **Deploy**.

Smoke: see `docs/ops/HOSTED_SMOKE.md`.

## 2. Deployments

Vercel automatically listens to the repository:
- **Production:** Pushes to the default branch (e.g., `main`) automatically trigger a production build.
- **Preview Environments:** Pushes to any other branch automatically create an isolated preview environment and attach the URL to the Pull Request.

## 3. Instant Rollbacks

If a bad deployment affects production:
1. Go to the Project dashboard in Vercel.
2. Navigate to the **Deployments** tab.
3. Locate the previous successful deployment that you want to revert to.
4. Click the three dots (`...`) next to it and select **Promote to Production** (or **Assign Custom Domains** to point the main URL to it).
5. Vercel rollbacks are instant because previous builds are cached and immediately served by the Edge network.

## 4. Log Drains & Monitoring

For pilot operations, Vercel's default runtime logs are ephemeral and hard to search. It is highly recommended to configure a Log Drain:
1. In the Vercel Dashboard, go to **Settings** -> **Log Drains**.
2. Vercel provides native integrations for providers like **BetterStack**, **Datadog**, or **Axiom**.
3. Axiom is recommended for Next.js as it offers a generous free tier and structured logging for Vercel apps.
4. Install the Axiom integration from the Vercel Marketplace. This will allow you to query frontend errors and API response times during the pilot phase.
