import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import select

from app.core import database
from app.models.events import PaymentStatus, WebhookEvent
from app.models.ledger import AccountBalance, LedgerEntry, LedgerEntryStatus
from app.models.outbox import OutboxEvent, OutboxStatus
from app.services.idempotency import IdempotencyService
from app.services.publisher import LedgerPublisher


class ReconciliationPipeline:
    """Settles payments into the ledger with idempotency and outbox safety."""

    def __init__(
        self,
        idempotency: IdempotencyService | None = None,
        publisher: LedgerPublisher | None = None,
    ) -> None:
        self._idempotency = idempotency or IdempotencyService()
        self._publisher = publisher or LedgerPublisher()

    def process(self, raw_payload: dict) -> dict:
        event = WebhookEvent.model_validate(raw_payload)

        if self._idempotency.is_duplicate(event.event_id):
            return {"status": "duplicate", "event_id": event.event_id}

        if not self._idempotency.try_acquire(event.event_id):
            return {"status": "duplicate_in_flight", "event_id": event.event_id}

        try:
            return self._settle(event)
        except Exception as exc:
            self._write_outbox(event, raw_payload, str(exc))
            self._idempotency.release(event.event_id)
            raise

    def _settle(self, event: WebhookEvent) -> dict:
        if event.status != PaymentStatus.SUCCEEDED:
            self._idempotency.mark_completed(event.event_id)
            return {"status": "skipped", "reason": event.status.value, "event_id": event.event_id}

        with database.session_scope() as session:
            existing = session.exec(
                select(LedgerEntry).where(LedgerEntry.transaction_id == event.transaction_id)
            ).first()
            if existing:
                self._idempotency.mark_completed(event.event_id)
                return {"status": "duplicate", "event_id": event.event_id}

            balance_row = session.exec(
                select(AccountBalance).where(AccountBalance.merchant_id == event.merchant_id)
            ).first()

            if balance_row is None:
                balance_row = AccountBalance(
                    merchant_id=event.merchant_id,
                    balance=Decimal("0"),
                    currency=event.currency,
                )
                session.add(balance_row)
                session.flush()

            new_balance = balance_row.balance + event.amount
            balance_row.balance = new_balance
            balance_row.updated_at = datetime.now(UTC)
            session.add(balance_row)

            entry = LedgerEntry(
                event_id=event.event_id,
                transaction_id=event.transaction_id,
                amount=event.amount,
                currency=event.currency,
                status=LedgerEntryStatus.SETTLED.value,
                merchant_id=event.merchant_id,
                customer_email=event.customer_email,
                running_balance=new_balance,
                settled_at=datetime.now(UTC),
            )
            session.add(entry)
            session.commit()

        self._idempotency.mark_completed(event.event_id)
        self._publisher.publish_balance_update(
            merchant_id=event.merchant_id,
            balance=new_balance,
            currency=event.currency,
            transaction_id=event.transaction_id,
            amount=event.amount,
            event_id=event.event_id,
        )

        return {
            "status": "settled",
            "event_id": event.event_id,
            "transaction_id": event.transaction_id,
            "balance": str(new_balance),
        }

    def _write_outbox(self, event: WebhookEvent, raw_payload: dict, error: str) -> None:
        try:
            with database.session_scope() as session:
                outbox = OutboxEvent(
                    event_id=event.event_id,
                    payload=json.dumps(raw_payload),
                    status=OutboxStatus.PENDING.value,
                    last_error=error[:2000],
                )
                session.add(outbox)
                session.commit()
        except Exception:
            pass

    def retry_outbox_batch(self, limit: int = 50) -> int:
        processed = 0
        with database.session_scope() as session:
            pending = session.exec(
                select(OutboxEvent)
                .where(OutboxEvent.status == OutboxStatus.PENDING.value)
                .limit(limit)
            ).all()

            for row in pending:
                try:
                    payload = json.loads(row.payload)
                    self.process(payload)
                    row.status = OutboxStatus.PROCESSED.value
                    row.processed_at = datetime.now(UTC)
                    processed += 1
                except Exception as exc:
                    row.retry_count += 1
                    row.last_error = str(exc)[:2000]
                    if row.retry_count >= 10:
                        row.status = OutboxStatus.FAILED.value
                session.add(row)
            session.commit()
        return processed
