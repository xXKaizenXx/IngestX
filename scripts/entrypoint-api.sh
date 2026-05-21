#!/bin/sh
set -eu

echo "Waiting for dependencies..."
python scripts/wait_for_services.py --timeout "${STARTUP_TIMEOUT:-90}"

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

WORKERS="${API_WORKERS:-2}"
echo "Starting API with ${WORKERS} worker(s)..."

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WORKERS}" \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}" \
  --log-level "${LOG_LEVEL:-info}"
