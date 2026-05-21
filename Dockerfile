# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY workers ./workers
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 ingestx \
    && useradd --uid 10001 --gid ingestx --create-home ingestx

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=ingestx:ingestx . .

RUN sed -i 's/\r$//' scripts/entrypoint-api.sh scripts/entrypoint-worker.sh scripts/start-render-free.sh \
    && chmod +x scripts/entrypoint-api.sh scripts/entrypoint-worker.sh scripts/start-render-free.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

USER ingestx
EXPOSE 8000

ENTRYPOINT ["./scripts/entrypoint-api.sh"]
