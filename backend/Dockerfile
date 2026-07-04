# libgomp1 is the OpenMP runtime xgboost's compiled extension needs at import
# time — without it, `import xgboost` fails inside this (Debian-based) image
# the same way it does on a fresh macOS install without `brew install libomp`.
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
WORKDIR /app

# ---- builder: installs prod-only deps + the project into a venv ----
FROM base AS builder
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev
COPY . .
RUN uv sync --frozen --no-dev

# ---- dev: full dep set (incl. ruff/mypy/pytest), used by docker-compose ----
# The named .venv volume in docker-compose persists across rebuilds, so
# `uv sync` also runs again at container startup to pick up dependency
# changes that happened after this image was built.
FROM base AS dev
COPY pyproject.toml uv.lock* ./
RUN uv sync
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- production: minimal runtime, no build tools, non-root ----
# This is the default target (last stage) so a plain `docker build .`,
# as CI and any PaaS building straight from this Dockerfile will do,
# produces the production image without needing --target.
FROM python:3.12-slim AS production
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
# A script file (rather than an inline shell string) so $PORT expansion,
# migrations, and the final `exec` (uvicorn takes PID 1 for correct SIGTERM
# handling) don't depend on however faithfully a PaaS's config layer
# reproduces shell quoting when passed through YAML.
CMD ["./docker-entrypoint.sh"]
