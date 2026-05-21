import structlog

from workers.pipeline import ReconciliationPipeline

logger = structlog.get_logger()
_pipeline = ReconciliationPipeline()


def process_webhook_event(raw_payload: dict) -> dict:
    """RQ entrypoint — heavy business logic runs off the HTTP thread."""
    logger.info("processing_event", event_id=raw_payload.get("event_id"))
    result = _pipeline.process(raw_payload)
    logger.info("event_processed", **result)
    return result


def retry_outbox_events(limit: int = 50) -> int:
    """Scheduled job to drain the transactional outbox after DB recovery."""
    count = _pipeline.retry_outbox_batch(limit=limit)
    logger.info("outbox_retry_complete", processed=count)
    return count
