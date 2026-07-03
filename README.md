# AdvisIQ

A multi-tenant SaaS platform for early identification of at-risk students, built on an XGBoost prediction model.

> All data in this repository is synthetic (every identifier is prefixed `SYNTH`). No real student data is ever committed.

## Status

Work in progress — built phase by phase. See [docs/architecture.md](docs/architecture.md) for the repository layout and [docs/decisions](docs/decisions) for the reasoning behind key choices.

- [x] Phase 1: Backend skeleton, auth, students API
- [x] Phase 2: Prediction service and frontend dashboard
- [ ] Phase 3: Docker, CI/CD, deployment
- [ ] Phase 4: MLOps and observability

> **On the ML model**: the project brief assumes an "existing validated XGBoost model," but this repo has no real student outcome data to validate against. `backend/scripts/train_risk_model.py` trains against an explicit, documented synthetic risk rule instead — it demonstrates the full pipeline (feature engineering → training → versioned artifact → serving) but has no real-world predictive validity. See that script's docstring for the exact rule.

## Setup

Requires Docker Desktop and Node.js.

1. Clone the repo and `cd` into it.
2. `cp .env.example .env` — for real deployments, replace `JWT_SECRET_KEY` with the output of `openssl rand -hex 32`.
3. `docker compose up -d --build` — starts Postgres and the API.
4. `docker compose exec backend alembic upgrade head` — applies the database schema.
5. Seed 500 synthetic students into a demo tenant, then score them:
   ```
   cd backend && DATABASE_URL="postgresql+asyncpg://advisiq:localdevpassword@localhost:5432/advisiq" \
     uv run python ../data/synth/generate_students.py --seed-db
   ```
   Register a user for tenant "SYNTH Demo University" via http://localhost:8000/docs (`POST /api/v1/auth/register`), then trigger batch scoring from the Admin page once the frontend is running (step 7).
6. Visit http://localhost:8000/docs for interactive API docs, or http://localhost:8000/health to confirm the API is up.
7. In a second terminal: `cd frontend && cp .env.local.example .env.local && npm install && npm run dev`, then visit http://localhost:3000.

### Running tests

```
docker compose up -d db
cd backend
DATABASE_URL="postgresql+asyncpg://advisiq:localdevpassword@localhost:5432/advisiq" uv run pytest
```

Tests run against a dedicated `advisiq_test` database (created automatically) so they never touch your dev data. Coverage must stay at or above 80% (currently ~97%, 45 tests). The risk/prediction tests use a deterministic stub model (see `tests/conftest.py`), not the real trained artifact.

## Tech stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- **Database**: PostgreSQL 16
- **ML**: XGBoost (synthetic demo model — see note above), MLflow (Phase 4)
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Auth**: JWT access/refresh tokens, bcrypt, role-based access control
- **Testing**: pytest, pytest-asyncio, httpx
- **DevOps**: Docker, docker compose, GitHub Actions

## License

MIT — see [LICENSE](LICENSE).
