from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"


class WebhookEvent(BaseModel):
    """Validated payment-gateway webhook payload."""

    event_id: str = Field(..., description="Unique idempotency key from provider")
    transaction_id: str
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="ZAR", min_length=3, max_length=3)
    status: PaymentStatus
    merchant_id: str
    customer_email: str | None = None
    metadata: dict = Field(default_factory=dict)
    received_at: datetime | None = None


class IngestResponse(BaseModel):
    accepted: bool = True
    event_id: str
    message: str = "Event queued for processing"
