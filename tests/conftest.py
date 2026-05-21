import json
import time
from contextlib import contextmanager

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.config import get_settings
from app.core.security import compute_signature
from app.main import app
from app.models import ledger, outbox  # noqa: F401 — register SQLModel metadata
from app.services.idempotency import IdempotencyService
from app.services.publisher import LedgerPublisher
from workers.pipeline import ReconciliationPipeline


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def test_engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def session_scope():
        session = Session(engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    monkeypatch.setattr("app.core.database.engine", engine)
    monkeypatch.setattr("app.core.database.session_scope", session_scope)
    return engine


@pytest.fixture
def pipeline(fake_redis, test_engine):
    return ReconciliationPipeline(
        idempotency=IdempotencyService(fake_redis),
        publisher=LedgerPublisher(fake_redis),
    )


@pytest.fixture
def client(fake_redis, test_engine, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "whsec_ci_secret")
    monkeypatch.setenv("WS_AUTH_TOKEN", "ci-stream-token")
    get_settings.cache_clear()

    monkeypatch.setattr(
        "app.services.rate_limiter.redis.from_url",
        lambda *a, **k: fake_redis,
    )
    monkeypatch.setattr(
        "app.services.queue.redis.from_url",
        lambda *a, **k: fake_redis,
    )
    monkeypatch.setattr(
        "app.services.idempotency.redis.from_url",
        lambda *a, **k: fake_redis,
    )

    from workers import tasks as worker_tasks
    from workers.pipeline import ReconciliationPipeline

    worker_tasks._pipeline = ReconciliationPipeline(
        idempotency=IdempotencyService(fake_redis),
        publisher=LedgerPublisher(fake_redis),
    )

    def _enqueue(payload):
        return worker_tasks.process_webhook_event(payload)

    monkeypatch.setattr(
        "app.services.queue.enqueue_webhook_event",
        lambda p: _enqueue(p) or "sync-job-id",
    )

    with TestClient(app) as c:
        yield c


def signed_ingest_request(
    payload: dict,
    secret: str = "whsec_ci_secret",
) -> tuple[bytes, dict[str, str]]:
    """Return body bytes and headers; body must be posted verbatim for signature match."""
    body = json.dumps(payload, separators=(",", ":")).encode()
    ts = str(int(time.time()))
    sig = compute_signature(body, secret, ts)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": ts,
        "X-Webhook-Signature": f"t={ts},v1={sig}",
    }
    return body, headers


@pytest.fixture
def sample_event():
    return {
        "event_id": "evt_test_001",
        "transaction_id": "txn_test_001",
        "amount": "150.00",
        "currency": "ZAR",
        "status": "succeeded",
        "merchant_id": "merchant_demo",
        "customer_email": "buyer@example.com",
        "metadata": {},
    }
