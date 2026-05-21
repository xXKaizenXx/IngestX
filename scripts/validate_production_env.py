#!/usr/bin/env python3
"""Verify .env.production and print derived connection strings."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    env_path = Path(".env.production")
    if not env_path.exists():
        print("Missing .env.production — copy from .env.production.example", file=sys.stderr)
        return 1

    env = load_env(env_path)
    pg_user = env.get("POSTGRES_USER", "ingestx")
    pg_pass = env.get("POSTGRES_PASSWORD", "")
    pg_db = env.get("POSTGRES_DB", "ingestx")
    redis_pass = env.get("REDIS_PASSWORD", "")

    expected_db = (
        f"postgresql+psycopg2://{quote_plus(pg_user)}:{quote_plus(pg_pass)}@postgres:5432/{pg_db}"
    )
    expected_redis = (
        f"redis://:{quote_plus(redis_pass)}@redis:6379/0"
        if redis_pass
        else "redis://redis:6379/0"
    )

    ok = True
    if env.get("DATABASE_URL") != expected_db:
        print("MISMATCH: DATABASE_URL does not match POSTGRES_* credentials")
        print(f"  expected: {expected_db}")
        print(f"  found:    {env.get('DATABASE_URL')}")
        ok = False
    else:
        print("OK  DATABASE_URL matches POSTGRES_*")

    if env.get("REDIS_URL") != expected_redis:
        print("MISMATCH: REDIS_URL does not match REDIS_PASSWORD")
        print(f"  expected: {expected_redis}")
        print(f"  found:    {env.get('REDIS_URL')}")
        ok = False
    else:
        print("OK  REDIS_URL matches REDIS_PASSWORD")

    for key in ("WEBHOOK_SECRET", "WS_AUTH_TOKEN", "POSTGRES_PASSWORD"):
        value = env.get(key, "")
        if not value or "CHANGE_ME" in value:
            print(f"FAIL: {key} is not set for production")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
