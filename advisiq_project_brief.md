# AdvisIQ Project Brief

A production grade, multi tenant SaaS platform for early identification of at risk students, built from an existing validated XGBoost prediction model. This document is the working specification to hand to Claude Code, one phase per session.

**Important constraints for all sessions:**
- All data in this repository is synthetic. Every dataset, student record, and identifier must carry the SYNTH prefix. No real student data is ever committed.
- The repository will be public on GitHub. Nothing sensitive (keys, credentials, institutional names) may appear in code, config, or commit history. Use a `.env` file and commit only `.env.example`.
- Every phase ends with passing tests and a working, runnable state. Do not move to the next phase with a broken build.

---

## 1. Product summary

AdvisIQ lets a university (a tenant) upload or sync student academic data, runs a risk prediction model over it, and presents advisors with a dashboard of risk tiers, cohort views, and intervention tracking.

Core user roles:
- **Advisor**: views assigned students, risk scores, and records interventions.
- **Admin**: manages users within their institution, uploads data, views institution wide analytics.

Out of scope for version 1: billing, email notifications, real time sync with student information systems.

## 2. Tech stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic migrations
- **Database**: PostgreSQL 16 (Docker for local dev)
- **ML**: XGBoost model loaded from a versioned artifact, MLflow for model registry (Phase 4)
- **Frontend**: Next.js with TypeScript, Tailwind CSS (Phase 2)
- **Auth**: JWT access and refresh tokens, bcrypt password hashing, role based access control
- **Testing**: pytest, pytest-asyncio, httpx test client, coverage target 80 percent on backend
- **DevOps**: Docker, docker compose for local, GitHub Actions for CI (lint, test, build), deployment target AWS or OCI free tier (Phase 3)
- **Quality tooling**: ruff (lint and format), mypy (type checking), pre-commit hooks

## 3. Repository structure

```
advisiq/
  README.md
  .env.example
  .gitignore
  .pre-commit-config.yaml
  docker-compose.yml
  backend/
    Dockerfile
    pyproject.toml
    alembic.ini
    alembic/
      versions/
    app/
      main.py
      config.py
      database.py
      models/            # SQLAlchemy models
        tenant.py
        user.py
        student.py
        risk_score.py
        intervention.py
      schemas/           # Pydantic request and response schemas
      api/
        deps.py          # auth and DB dependencies
        v1/
          auth.py
          students.py
          risk.py
          interventions.py
          admin.py
      services/          # business logic, no FastAPI imports here
        prediction.py
        ingestion.py
      ml/
        model_loader.py
        artifacts/       # versioned model files, gitignored if large
    tests/
      conftest.py
      test_auth.py
      test_students.py
      test_risk.py
      test_ingestion.py
  frontend/              # created in Phase 2
  data/
    synth/               # synthetic data generation scripts and samples
      generate_students.py
  .github/
    workflows/
      ci.yml
  docs/
    architecture.md
    decisions/           # short ADRs, one file per significant choice
```

## 4. Data model (initial)

- **tenants**: id, name, created_at
- **users**: id, tenant_id, email, hashed_password, role (advisor or admin), created_at
- **students**: id, tenant_id, synth_student_code, programme, year_of_study, demographic and academic feature columns used by the model
- **risk_scores**: id, student_id, model_version, score (0 to 1), tier (low, medium, high), scored_at
- **interventions**: id, student_id, advisor_id, type, notes, status, created_at

Every table with tenant scoped data carries tenant_id, and every query in the API must filter by the authenticated user's tenant. Write a test that proves cross tenant access is impossible.

## 5. Phase briefs

Give Claude Code one phase per session. Each brief below is written to be pasted directly.

### Phase 1: Backend skeleton, auth, and students API (weeks 1 to 4)

> Set up the backend of a project called AdvisIQ following the repository structure in docs/architecture.md. Use FastAPI, SQLAlchemy 2.x, Alembic, and PostgreSQL via docker compose. Implement: (1) tenant, user, and student models with an initial Alembic migration; (2) JWT auth with register, login, and refresh endpoints, bcrypt hashing, and role based access control with advisor and admin roles; (3) CRUD endpoints for students, tenant scoped so users only ever see their own tenant's records; (4) a synthetic data script in data/synth that generates 500 students with a SYNTH prefix on every identifier; (5) pytest suite with httpx covering auth flows, student CRUD, and a test proving cross tenant access returns 404 or 403. Configure ruff, mypy, and pre-commit. Everything must run with docker compose up and pass pytest.

Definition of done: `docker compose up` starts API and database, `pytest` passes, coverage at or above 80 percent, README documents setup in under ten steps.

### Phase 2: Prediction service and frontend dashboard (weeks 5 to 9)

> Add the ML layer and frontend to AdvisIQ. Backend: (1) a prediction service in app/services/prediction.py that loads the XGBoost artifact through app/ml/model_loader.py, scores a student or a batch, writes rows to risk_scores with a model_version string, and maps scores to low, medium, and high tiers with thresholds in config; (2) endpoints to trigger batch scoring (admin only) and to fetch risk scores per student and per cohort; (3) tests using a small deterministic stub model so tests do not depend on the real artifact. Frontend: a Next.js and TypeScript app with login, an advisor dashboard showing students grouped by risk tier with filtering by programme and year, a student detail page with score history and an intervention log form, and an admin page for user management and triggering batch scoring. Use the API only, no direct DB access.

Definition of done: an advisor can log in, see tiered students, open a student, and record an intervention end to end against synthetic data.

### Phase 3: Docker, CI/CD, and deployment (weeks 10 to 13)

> Productionise AdvisIQ. (1) Multi stage Dockerfiles for backend and frontend; (2) GitHub Actions workflow that runs ruff, mypy, and pytest on every push and pull request, builds images on merge to main, and deploys to the chosen cloud target; (3) environment based config with no secrets in the repo, using GitHub Actions secrets; (4) structured JSON logging in the backend and Sentry integration behind an env flag; (5) a deployed public demo seeded with synthetic data, URL recorded in the README with demo credentials.

Definition of done: green CI badge in the README, a live URL, and a fresh clone deploys with documented steps.

### Phase 4: MLOps and observability (weeks 14 to 18)

> Add MLOps to AdvisIQ. (1) Register the model in MLflow and load by version through the model registry instead of a raw file path; (2) a retraining script that trains on the synthetic dataset, evaluates against the current production model, and promotes only on improvement, runnable locally and as a scheduled GitHub Actions workflow; (3) drift monitoring that compares recent input feature distributions to the training distribution and exposes a drift status endpoint; (4) basic metrics (request counts, latency, scoring volume) exposed for scraping; (5) docs/architecture.md updated with a final architecture diagram and an ADR for each major decision made across the project.

Definition of done: model version visible in API responses, retraining workflow runs green, drift endpoint returns meaningful output on shifted synthetic data.

## 6. Portfolio finishing checklist

- README with problem statement, architecture diagram, screenshots, live demo link, and a short section on what you would do differently
- All commits meaningful, no giant single commits, branch and pull request workflow used from Phase 2 onward
- LICENSE file (MIT) and a short CONTRIBUTING note
- A one page write up mapping each part of the project to skills named in New Zealand software engineer job advertisements
