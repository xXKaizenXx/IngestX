import redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class IdempotencyService:
    """Distributed idempotency via Redis SET NX + TTL."""

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._redis = redis_client or redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl = settings.idempotency_ttl_seconds
        self._prefix = "idempotency:event:"

    def _key(self, event_id: str) -> str:
        return f"{self._prefix}{event_id}"

    def try_acquire(self, event_id: str) -> bool:
        """Return True if this is the first time we see event_id."""
        try:
            return bool(self._redis.set(self._key(event_id), "processing", nx=True, ex=self._ttl))
        except RedisError:
            # Fail open on Redis outage so ingestion isn't blocked; worker re-checks.
            return True

    def mark_completed(self, event_id: str) -> None:
        try:
            self._redis.set(self._key(event_id), "completed", ex=self._ttl)
        except RedisError:
            pass

    def is_duplicate(self, event_id: str) -> bool:
        try:
            value = self._redis.get(self._key(event_id))
            return value == "completed"
        except RedisError:
            return False

    def release(self, event_id: str) -> None:
        try:
            self._redis.delete(self._key(event_id))
        except RedisError:
            pass
