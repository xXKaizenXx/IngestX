from fastapi import APIRouter, Depends
from pydantic import BaseModel
from rq import Queue
from sqlmodel import Session, func, select

from app.core.config import get_settings
from app.core.database import engine, get_session
from app.models.ledger import AccountBalance, LedgerEntry
from app.models.outbox import OutboxEvent, OutboxStatus
from app.routers.ledger import require_stream_token
from app.services.queue import get_redis_connection

router = APIRouter(prefix="/api/v1/system", tags=["system"])


class SystemStatusResponse(BaseModel):
    api: str
    database: str
    redis: str
    queue_name: str
    queue_depth: int
    outbox_pending: int
    ledger_entries: int
    active_merchants: int


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(
    session: Session = Depends(get_session),
    _: None = Depends(require_stream_token),
) -> SystemStatusResponse:
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception:
        db_status = "error"

    redis_status = "ok"
    queue_depth = 0
    try:
        conn = get_redis_connection()
        conn.ping()
        queue = Queue(get_settings().rq_queue_name, connection=conn)
        queue_depth = queue.count
    except Exception:
        redis_status = "error"

    outbox_pending = session.exec(
        select(func.count()).select_from(OutboxEvent).where(
            OutboxEvent.status == OutboxStatus.PENDING.value
        )
    ).one()
    ledger_entries = session.exec(select(func.count()).select_from(LedgerEntry)).one()
    active_merchants = session.exec(select(func.count()).select_from(AccountBalance)).one()

    return SystemStatusResponse(
        api="ok",
        database=db_status,
        redis=redis_status,
        queue_name=get_settings().rq_queue_name,
        queue_depth=queue_depth,
        outbox_pending=outbox_pending or 0,
        ledger_entries=ledger_entries or 0,
        active_merchants=active_merchants or 0,
    )
