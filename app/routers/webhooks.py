import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import ValidationError

from app.core.security import require_webhook_signature
from app.models.events import IngestResponse, WebhookEvent
from app.services import queue as queue_service
from app.services.rate_limiter import RedisRateLimiter

router = APIRouter(prefix="/api/v1", tags=["ingestion"])
_rate_limiter = RedisRateLimiter()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="High-speed webhook ingestion",
)
async def ingest_webhook(raw_body: bytes = Depends(require_webhook_signature)) -> IngestResponse:
    """
    Phase 1: validate signature, enqueue raw event, return immediately.
    No database writes or business logic on the request thread.
    """
    _rate_limiter.check()

    try:
        payload = json.loads(raw_body)
        event = WebhookEvent.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        from fastapi import HTTPException

        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    event_payload = event.model_dump(mode="json")
    event_payload["received_at"] = datetime.now(UTC).isoformat()

    queue_service.enqueue_webhook_event(event_payload)

    return IngestResponse(event_id=event.event_id)
