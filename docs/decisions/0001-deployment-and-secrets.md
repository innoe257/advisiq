# ADR 0001: Deployment target and secrets handling

## Status

Accepted

## Context

The project brief calls for deploying to "AWS or OCI free tier." Both are legitimate, but a raw VM/VPC/IAM setup on either is significant DevOps overhead relative to the learning value at this stage of the project, and risks eating the whole session without producing a working live URL.

## Decision

Deploy the backend + Postgres to **Render** (via a `render.yaml` blueprint — Docker-based, builds straight from `backend/Dockerfile`'s `production` stage) and the frontend to **Vercel** (zero-config for Next.js, built by the same team). Both have free tiers that don't expire on a timer, unlike Fly.io (now requires a card on file) or a raw Render free Postgres (historically time-limited).

## Secrets

No GitHub Actions secrets are required for this repository as it stands:

- The **test** jobs (`ruff`/`mypy`/`pytest`) use throwaway values (`JWT_SECRET_KEY: ci-test-secret-not-for-production`, a fresh Postgres service container) defined directly in the workflow — nothing sensitive.
- The **build-images** job publishes to GHCR using the built-in `secrets.GITHUB_TOKEN`, which GitHub provisions automatically per run; no manual secret setup needed.
- Real secrets (`JWT_SECRET_KEY`, `DATABASE_URL`, `SENTRY_DSN`) are configured as environment variables directly in the Render and Vercel dashboards, not passed through GitHub Actions at all — deployment happens via each platform's own git integration (they watch the repo and build on push), not via a GitHub Actions deploy step.

## Consequences

If a later phase adds GitHub Actions-triggered deployment (e.g., a retraining workflow in Phase 4 that redeploys via Render's or Vercel's API), that would introduce the first real need for repo secrets (`RENDER_API_KEY`, `VERCEL_TOKEN`) — revisit this ADR then.
