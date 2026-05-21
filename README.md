# IngestX

High-throughput webhook ingestion engine with real-time ledger reconciliation — built to demonstrate production patterns expected at intermediate backend roles (fintech / e-commerce).

## Architecture

```
[Payment Gateway Webhooks]
          │
          ▼
┌─────────────────────┐
│  FastAPI (Phase 1)  │  Signature verify → RQ enqueue → HTTP 202
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│     Redis Queue     │  Event buffer (no dropped requests)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│    RQ Workers       │  Idempotency → Ledger → Pub/Sub
└─────┬─────────┬─────┘
      │         │
      ▼         ▼
   Redis    PostgreSQL (+ Outbox table)
                  │
                  ▼
            WebSocket stream → React Dashboard
```

## Features

| Milestone | Implementation |
|-----------|----------------|
| Ultra-fast ingestion | `POST /api/v1/ingest` returns **202** immediately; no DB on request thread |
| Rate limiting | Redis sliding-window limiter (`INGEST_RATE_LIMIT_PER_SECOND`) |
| Signature verification | Stripe-style HMAC-SHA256 (`X-Webhook-Signature`, `X-Webhook-Timestamp`) |
| Distributed workers | RQ worker pool consuming `webhook_events` queue |
| Idempotency | Redis `SET NX` locks keyed by `event_id` + DB unique `transaction_id` |
| Transactional outbox | Failed settlements persisted to `outbox_events`; `outbox-retry` service drains queue |
| Live dashboard stream | `WS /api/v1/stream?token=...` fed by Redis Pub/Sub |
| **Ledger Command Center** | React dashboard — sidebar nav, search/filter/export, system health, settings |

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

- API: http://localhost:8000/docs
- **Dashboard:** http://localhost:3000
- Health: http://localhost:8000/health

### Local development

```bash
# Start Postgres + Redis
docker compose up postgres redis -d

# Install
pip install -e ".[dev]"

# API
uvicorn app.main:app --reload

# Worker (separate terminal)
rq worker webhook_events

# Dashboard (separate terminal)
cd dashboard && cp .env.example .env && npm install && npm run dev
```

Copy `.env.example` to `.env` and adjust secrets. Dashboard env is in `dashboard/.env.example`.

**Production deployment:** see [DEPLOYMENT.md](DEPLOYMENT.md).

## API

### Ingest webhook

```http
POST /api/v1/ingest
X-Webhook-Timestamp: <unix_seconds>
X-Webhook-Signature: t=<ts>,v1=<hmac_hex>
Content-Type: application/json

{
  "event_id": "evt_123",
  "transaction_id": "txn_456",
  "amount": "150.00",
  "currency": "ZAR",
  "status": "succeeded",
  "merchant_id": "merchant_demo"
}
```

Response: `202 Accepted`

```json
{ "accepted": true, "event_id": "evt_123", "message": "Event queued for processing" }
```

### Live balance stream

```text
ws://localhost:8000/api/v1/stream?token=<WS_AUTH_TOKEN>&merchant_id=merchant_demo
```

### Ledger read API (dashboard bootstrap)

```http
GET /api/v1/ledger/{merchant_id}/balance
GET /api/v1/ledger/{merchant_id}/transactions?limit=50
GET /api/v1/system/status
X-Stream-Token: <WS_AUTH_TOKEN>
```

### Send a test webhook

```bash
PYTHONPATH=. python scripts/send_test_webhook.py
```

## Testing

```bash
pytest tests/ -v
ruff check app workers tests
```

## Project structure

```
ingestx/
├── app/           # FastAPI ingestion layer
├── dashboard/     # React Ledger Command Center (Vite + TypeScript)
├── workers/       # RQ tasks + reconciliation pipeline
├── tests/         # Ingestion + idempotency + outbox tests
├── scripts/       # Utilities
└── docker-compose.yml
```

## Interview talking points

1. **Why 202 + queue?** Keeps the HTTP thread O(1); gateways retry on timeout — you must ack fast.
2. **Why Redis idempotency + DB unique constraint?** Defense in depth — Redis for speed, Postgres for durability.
3. **Why outbox?** If the ledger DB fails mid-write, the event is not lost; the retry loop replays safely.
4. **Why Pub/Sub + WebSocket?** Decouples write path from fan-out to dashboards without polling.
5. **Why bootstrap REST + live WS?** Dashboard loads historical ledger on mount, then streams deltas — standard enterprise pattern.

## License

MIT
