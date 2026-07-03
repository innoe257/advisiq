# AdvisIQ

A multi-tenant SaaS platform for early identification of at-risk students, built on an XGBoost prediction model.

> All data in this repository is synthetic (every identifier is prefixed `SYNTH`). No real student data is ever committed.

## Status

Work in progress — built phase by phase. See [docs/architecture.md](docs/architecture.md) for the repository layout and [docs/decisions](docs/decisions) for the reasoning behind key choices.

- [ ] Phase 1: Backend skeleton, auth, students API
- [ ] Phase 2: Prediction service and frontend dashboard
- [ ] Phase 3: Docker, CI/CD, deployment
- [ ] Phase 4: MLOps and observability

## Setup

_Documented once Phase 1 is complete._

## Tech stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- **Database**: PostgreSQL 16
- **ML**: XGBoost, MLflow (Phase 4)
- **Frontend**: Next.js, TypeScript, Tailwind CSS (Phase 2)
- **Auth**: JWT access/refresh tokens, bcrypt, role-based access control
- **Testing**: pytest, pytest-asyncio, httpx
- **DevOps**: Docker, docker compose, GitHub Actions

## License

MIT — see [LICENSE](LICENSE).
