FROM python:3.12-slim

# libgomp1 is the OpenMP runtime xgboost's compiled extension needs at import
# time — without it, `import xgboost` fails inside this (Debian-based) image
# the same way it does on a fresh macOS install without `brew install libomp`.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project

COPY . .
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
