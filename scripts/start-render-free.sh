#!/bin/sh
# Single-container mode for Render free tier (workers are not free as separate services).
set -eu

python scripts/wait_for_services.py --timeout "${STARTUP_TIMEOUT:-120}"

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade head
fi

echo "Starting RQ worker in background..."
rq worker "${RQ_QUEUE_NAME:-webhook_events}" --url "${REDIS_URL}" &

echo "Starting outbox retry loop in background..."
(
  while true; do
    python -c 'from workers.tasks import retry_outbox_events; retry_outbox_events()' || true
    sleep "${OUTBOX_RETRY_INTERVAL:-30}"
  done
) &

echo "Starting API on port ${PORT:-8000}..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}" \
  --log-level "${LOG_LEVEL:-info}"
