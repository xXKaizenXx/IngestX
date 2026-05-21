
import redis
from rq import Queue

from app.core.config import get_settings


def get_redis_connection() -> redis.Redis:
    return redis.from_url(get_settings().redis_url)


def get_task_queue() -> Queue:
    settings = get_settings()
    conn = get_redis_connection()
    return Queue(settings.rq_queue_name, connection=conn)


def enqueue_webhook_event(raw_payload: dict) -> str:
    """Push validated event onto RQ; returns job id."""
    queue = get_task_queue()
    job = queue.enqueue(
        "workers.tasks.process_webhook_event",
        raw_payload,
        job_timeout=120,
        result_ttl=3600,
        failure_ttl=86400,
    )
    return job.id
