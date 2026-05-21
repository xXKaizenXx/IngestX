from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import verify_ws_token
from app.models.ledger import AccountBalance, LedgerEntry

router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])


class BalanceResponse(BaseModel):
    merchant_id: str
    balance: str
    currency: str
    updated_at: str | None


class TransactionItem(BaseModel):
    transaction_id: str
    event_id: str
    amount: str
    currency: str
    status: str
    running_balance: str
    settled_at: str


class TransactionListResponse(BaseModel):
    merchant_id: str
    items: list[TransactionItem]
    total: int


def require_stream_token(
    x_stream_token: Annotated[str | None, Header(alias="X-Stream-Token")] = None,
    token: Annotated[str | None, Query()] = None,
) -> None:
    verify_ws_token(x_stream_token or token)


@router.get("/{merchant_id}/balance", response_model=BalanceResponse)
def get_balance(
    merchant_id: str,
    session: Session = Depends(get_session),
    _: None = Depends(require_stream_token),
) -> BalanceResponse:
    row = session.exec(
        select(AccountBalance).where(AccountBalance.merchant_id == merchant_id)
    ).first()
    if row is None:
        return BalanceResponse(
            merchant_id=merchant_id,
            balance="0.00",
            currency="ZAR",
            updated_at=None,
        )
    return BalanceResponse(
        merchant_id=row.merchant_id,
        balance=str(row.balance),
        currency=row.currency,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@router.get("/{merchant_id}/transactions", response_model=TransactionListResponse)
def list_transactions(
    merchant_id: str,
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    _: None = Depends(require_stream_token),
) -> TransactionListResponse:
    rows = session.exec(
        select(LedgerEntry)
        .where(LedgerEntry.merchant_id == merchant_id)
        .order_by(desc(LedgerEntry.settled_at))
        .limit(limit)
    ).all()

    items = [
        TransactionItem(
            transaction_id=r.transaction_id,
            event_id=r.event_id,
            amount=str(r.amount),
            currency=r.currency,
            status=r.status,
            running_balance=str(r.running_balance),
            settled_at=r.settled_at.isoformat(),
        )
        for r in rows
    ]
    return TransactionListResponse(merchant_id=merchant_id, items=items, total=len(items))
