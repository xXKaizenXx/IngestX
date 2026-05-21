#!/bin/sh
set -eu

python scripts/wait_for_services.py --timeout "${STARTUP_TIMEOUT:-90}"

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade head
fi

exec rq worker "${RQ_QUEUE_NAME:-webhook_events}" --url "${REDIS_URL}"
