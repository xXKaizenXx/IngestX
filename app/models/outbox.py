from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEvent(SQLModel, table=True):
    """Transactional outbox — survives DB outages during worker processing."""

    __tablename__ = "outbox_events"

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(index=True)
    payload: str
    status: str = Field(default=OutboxStatus.PENDING.value, index=True)
    retry_count: int = Field(default=0)
    last_error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
