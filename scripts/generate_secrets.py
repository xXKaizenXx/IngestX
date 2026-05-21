#!/usr/bin/env python3
"""Generate cryptographically secure secrets for production .env files."""

import secrets


def main() -> None:
    print("# Paste these into .env.production")
    print(f"WEBHOOK_SECRET={secrets.token_urlsafe(32)}")
    print(f"WS_AUTH_TOKEN={secrets.token_urlsafe(32)}")
    print(f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}")
    print(f"REDIS_PASSWORD={secrets.token_urlsafe(24)}")


if __name__ == "__main__":
    main()
