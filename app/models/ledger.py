from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlmodel import Field, SQLModel, UniqueConstraint


class LedgerEntryStatus(StrEnum):
    SETTLED = "settled"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class LedgerEntry(SQLModel, table=True):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_transaction_id"),)

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(index=True)
    transaction_id: str = Field(index=True)
    amount: Decimal = Field(max_digits=18, decimal_places=2)
    currency: str = Field(default="ZAR", max_length=3)
    status: str
    merchant_id: str = Field(index=True)
    customer_email: str | None = None
    running_balance: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)
    settled_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccountBalance(SQLModel, table=True):
    __tablename__ = "account_balances"

    id: int | None = Field(default=None, primary_key=True)
    merchant_id: str = Field(unique=True, index=True)
    balance: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)
    currency: str = Field(default="ZAR", max_length=3)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
