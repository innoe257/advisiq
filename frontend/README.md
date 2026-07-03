# AdvisIQ frontend

Next.js (App Router) + TypeScript + Tailwind CSS dashboard for advisors and admins. See the [repo root README](../README.md) for full project context.

## Setup

1. `cp .env.local.example .env.local` — points at the backend API (defaults to `http://localhost:8000/api/v1`).
2. `npm install`
3. `npm run dev` — requires the backend running (see root README).

## Structure

- `src/lib/api/` — typed wrappers around each backend resource (auth, students, risk, interventions), all going through `client.ts`'s `apiFetch`, which handles attaching the access token and transparently refreshing it on a 401.
- `src/lib/auth-context.tsx` — React context exposing the current user, `login()`, and `logout()`.
- `src/app/(protected)/` — route group for pages that require auth; its `layout.tsx` redirects to `/login` if unauthenticated and renders the shared nav bar.
