from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.models.ledger import AccountBalance, LedgerEntry
from app.models.outbox import OutboxEvent, OutboxStatus
from tests.conftest import signed_ingest_request


def test_settlement_updates_balance(pipeline, sample_event, test_engine):
    result = pipeline.process(sample_event)
    assert result["status"] == "settled"
    assert result["balance"] == "150.00"

    with Session(test_engine) as session:
        balance = session.exec(
            select(AccountBalance).where(AccountBalance.merchant_id == "merchant_demo")
        ).one()
        assert balance.balance == Decimal("150.00")

        entry = session.exec(
            select(LedgerEntry).where(LedgerEntry.transaction_id == "txn_test_001")
        ).one()
        assert entry.running_balance == Decimal("150.00")


def test_idempotency_discards_duplicate_event(pipeline, sample_event):
    first = pipeline.process(sample_event)
    second = pipeline.process(sample_event)
    assert first["status"] == "settled"
    assert second["status"] == "duplicate"


def test_duplicate_transaction_id_rejected(pipeline, sample_event):
    pipeline.process(sample_event)
    duplicate = {**sample_event, "event_id": "evt_different_id"}
    result = pipeline.process(duplicate)
    assert result["status"] == "duplicate"


def test_outbox_retry_drains_pending(pipeline, sample_event, test_engine, monkeypatch):
    call_count = {"n": 0}
    original_settle = pipeline._settle

    def flaky_settle(event):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ConnectionError("database unavailable")
        return original_settle(event)

    monkeypatch.setattr(pipeline, "_settle", flaky_settle)

    with pytest.raises(ConnectionError):
        pipeline.process(sample_event)

    with Session(test_engine) as session:
        pending = session.exec(select(OutboxEvent)).all()
        assert len(pending) == 1
        assert pending[0].status == OutboxStatus.PENDING.value

    processed = pipeline.retry_outbox_batch()
    assert processed == 1

    with Session(test_engine) as session:
        outbox = session.exec(select(OutboxEvent)).one()
        assert outbox.status == OutboxStatus.PROCESSED.value


def test_end_to_end_ingest_settles_ledger(client, sample_event, test_engine):
    body, headers = signed_ingest_request(sample_event)
    response = client.post("/api/v1/ingest", content=body, headers=headers)
    assert response.status_code == 202

    with Session(test_engine) as session:
        entry = session.exec(
            select(LedgerEntry).where(LedgerEntry.event_id == sample_event["event_id"])
        ).one()
        assert entry.amount == Decimal("150.00")
