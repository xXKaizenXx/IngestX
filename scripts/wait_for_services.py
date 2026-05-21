#!/usr/bin/env python3
"""Block until Postgres and Redis are reachable."""

import argparse
import sys
import time

import redis
from sqlalchemy import create_engine, text

from app.core.config import get_settings


def wait_for_postgres(timeout: int) -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Postgres is ready")
            return
        except Exception as exc:
            print(f"Waiting for Postgres... ({exc})")
            time.sleep(2)
    raise TimeoutError("Postgres did not become ready in time")


def wait_for_redis(timeout: int) -> None:
    settings = get_settings()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = redis.from_url(settings.redis_url)
            client.ping()
            print("Redis is ready")
            return
        except Exception as exc:
            print(f"Waiting for Redis... ({exc})")
            time.sleep(2)
    raise TimeoutError("Redis did not become ready in time")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    try:
        wait_for_postgres(args.timeout)
        wait_for_redis(args.timeout)
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
