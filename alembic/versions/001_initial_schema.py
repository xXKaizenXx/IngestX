"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("transaction_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("merchant_id", sa.String(), nullable=False),
        sa.Column("customer_email", sa.String(), nullable=True),
        sa.Column("running_balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("settled_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id", name="uq_transaction_id"),
    )
    op.create_index("ix_ledger_entries_event_id", "ledger_entries", ["event_id"])
    op.create_index("ix_ledger_entries_transaction_id", "ledger_entries", ["transaction_id"])
    op.create_index("ix_ledger_entries_merchant_id", "ledger_entries", ["merchant_id"])

    op.create_table(
        "account_balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.String(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id"),
    )
    op.create_index("ix_account_balances_merchant_id", "account_balances", ["merchant_id"])

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("payload", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_events_event_id", "outbox_events", ["event_id"])
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_outbox_events_status", table_name="outbox_events")
    op.drop_index("ix_outbox_events_event_id", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_account_balances_merchant_id", table_name="account_balances")
    op.drop_table("account_balances")
    op.drop_index("ix_ledger_entries_merchant_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_transaction_id", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_event_id", table_name="ledger_entries")
    op.drop_table("ledger_entries")
