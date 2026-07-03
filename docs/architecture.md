# Architecture

## Repository structure

```
.
├── README.md
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── student.py
│   │   │   ├── risk_score.py
│   │   │   └── intervention.py
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── api/
│   │   │   ├── deps.py         # auth and DB dependencies
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── students.py
│   │   │       ├── risk.py
│   │   │       ├── interventions.py
│   │   │       └── admin.py
│   │   ├── services/           # business logic, no FastAPI imports
│   │   │   ├── prediction.py
│   │   │   └── ingestion.py
│   │   └── ml/
│   │       ├── model_loader.py
│   │       └── artifacts/      # versioned model files, gitignored
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_students.py
│       ├── test_risk.py
│       └── test_ingestion.py
├── frontend/                    # created in Phase 2
├── data/
│   └── synth/                   # synthetic data generation scripts/samples
│       └── generate_students.py
├── .github/
│   └── workflows/
│       └── ci.yml
└── docs/
    ├── architecture.md
    └── decisions/                # one short ADR per significant choice
```

## Multi-tenancy

Every tenant-scoped table (`students`, `risk_scores`, `interventions`, and `users`) carries a `tenant_id`. Every API query filters by the authenticated user's tenant — there is no cross-tenant read or write path. This is enforced at the query layer, not just the API layer, and is covered by an explicit test proving cross-tenant access is impossible (returns 404/403).

## Data model (initial)

- **tenants**: id, name, created_at
- **users**: id, tenant_id, email, hashed_password, role (advisor | admin), created_at
- **students**: id, tenant_id, synth_student_code, programme, year_of_study, feature columns used by the model
- **risk_scores**: id, student_id, model_version, score (0–1), tier (low | medium | high), scored_at
- **interventions**: id, student_id, advisor_id, type, notes, status, created_at

## Phases

1. Backend skeleton, auth, students API
2. Prediction service and frontend dashboard
3. Docker, CI/CD, deployment
4. MLOps and observability

Decisions made along the way are recorded as short ADRs in [decisions/](decisions/).
