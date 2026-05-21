import time

import redis
from fastapi import HTTPException, status

from app.core.config import get_settings


class RedisRateLimiter:
    """Token-bucket style limiter using a sliding 1-second window in Redis."""

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)
        self._limit = settings.ingest_rate_limit_per_second
        self._prefix = "ratelimit:ingest:"

    def check(self, client_key: str = "global") -> None:
        now = int(time.time())
        key = f"{self._prefix}{client_key}:{now}"
        try:
            count = self._redis.incr(key)
            if count == 1:
                self._redis.expire(key, 2)
            if count > self._limit:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Ingestion rate limit exceeded",
                )
        except redis.RedisError:
            # Degrade gracefully if Redis is unavailable
            pass
