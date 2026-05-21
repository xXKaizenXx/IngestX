# Production Deployment Guide

This guide takes IngestX from local development to a production deployment on a VPS or managed platform.

## Pre-deploy checklist

Before going live, complete every item:

- [ ] **Generate secrets** (never use defaults in production)
  ```bash
  python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
  python -c "import secrets; print('WS_AUTH_TOKEN=' + secrets.token_urlsafe(32))"
  ```
- [ ] Set `ENVIRONMENT=production` (enforced secret validation + disables `/docs`)
- [ ] Set strong `POSTGRES_PASSWORD` and optional `REDIS_PASSWORD`
- [ ] Set `CORS_ORIGINS` to your real dashboard URL (e.g. `https://ingestx.yourdomain.com`)
- [ ] Point payment gateway webhooks to `https://yourdomain.com/api/v1/ingest`
- [ ] Run the test suite: `pytest tests/ -v`
- [ ] Build dashboard: `cd dashboard && npm run build`

## Architecture (production)

```
Internet
   │
   ▼
 Caddy (TLS :443)
   ├── /api/*  → FastAPI (multi-worker uvicorn)
   └── /*      → React dashboard (nginx)
         │
         ├── PostgreSQL (persistent volume)
         ├── Redis (queue + pub/sub + idempotency)
         ├── RQ workers (×N replicas)
         └── Outbox retry loop
```

---

## Option A — Docker Compose on a VPS (recommended)

Best for: DigitalOcean, Hetzner, AWS EC2, any Linux server with Docker.

### 1. Prepare the server

```bash
# Ubuntu/Debian example
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
# Log out and back in
```

### 2. Clone and configure

```bash
git clone <your-repo> ingestx && cd ingestx
cp .env.production.example .env.production
nano .env.production   # fill all CHANGE_ME values
```

**Important:** `DATABASE_URL` must use the `postgresql+psycopg2://` driver prefix.

### 3. DNS

Point an **A record** for `ingestx.yourdomain.com` to your server IP.

### 4. Deploy

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Scale workers for higher throughput:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --scale worker=3
```

### 5. Verify

```bash
curl -s https://ingestx.yourdomain.com/health
curl -s https://ingestx.yourdomain.com/ready
```

Open `https://ingestx.yourdomain.com` — dashboard should load with live connection.

Send a test webhook (update secret to match production):

```bash
WEBHOOK_SECRET=<your-secret> PYTHONPATH=. python scripts/send_test_webhook.py \
  --url https://ingestx.yourdomain.com/api/v1/ingest
```

### 6. Operations

| Task | Command |
|------|---------|
| View logs | `docker compose -f docker-compose.prod.yml logs -f api worker` |
| Restart API | `docker compose -f docker-compose.prod.yml restart api` |
| Run migrations | `docker compose -f docker-compose.prod.yml exec api alembic upgrade head` |
| Backup Postgres | `docker compose -f docker-compose.prod.yml exec postgres pg_dump -U ingestx ingestx > backup.sql` |

---

## Option B — Render (managed PaaS)

| Blueprint | Cost | Use when |
|-----------|------|----------|
| **`render.free.yaml`** | $0 (Hobby) | Portfolio / demo — no credit card |
| **`render.yaml`** | Paid (`starter` plans) | Production with separate workers |

**Why Render asked for payment:** `render.yaml` sets `plan: starter` on 5 resources and includes **2 background workers** — workers cannot use Render’s free tier.

### Free deploy (no payment)

1. Push repo to GitHub
2. Render → **New Blueprint** → set **Blueprint Path** to `render.free.yaml`
3. After deploy, set `CORS_ORIGINS` and `VITE_STREAM_TOKEN` (see below)

**Free tier limits:** web spins down after 15 min idle (~1 min cold start), Postgres expires in 30 days, 1 free Redis instance, 750 instance-hours/month.

### Paid deploy (`render.yaml`)

1. Add payment method in Render
2. Use default Blueprint path `render.yaml`
3. Set `CORS_ORIGINS` → `https://ingestx-dashboard.onrender.com`
4. Set `VITE_STREAM_TOKEN` on dashboard → same as API `WS_AUTH_TOKEN`

---

## Option C — Railway / Fly.io

### Railway

1. New project → Add PostgreSQL, Redis, and Docker services
2. Set environment variables from `.env.production.example`
3. Deploy API with `Dockerfile`, workers with `dockerCommand: ./scripts/entrypoint-worker.sh`

### Fly.io

```bash
fly launch --dockerfile Dockerfile
fly secrets set WEBHOOK_SECRET=... WS_AUTH_TOKEN=... ENVIRONMENT=production
fly postgres create && fly redis create
fly deploy
```

---

## Database migrations

Production uses **Alembic** (not `create_all`). Migrations run automatically on API startup.

Manual migration:

```bash
alembic upgrade head          # local
docker compose ... exec api alembic upgrade head   # production
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## Health probes

| Endpoint | Purpose | Success |
|----------|---------|---------|
| `GET /health` | Liveness — process is up | `200 {"status":"ok"}` |
| `GET /ready` | Readiness — DB + Redis reachable | `200 {"status":"ready"}` |

Configure your load balancer / orchestrator to use `/ready` for traffic routing.

---

## Security hardening summary

| Control | Implementation |
|---------|----------------|
| Secret validation | App refuses to start in `production` with default secrets |
| API docs disabled | `/docs` hidden when `ENVIRONMENT=production` |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, etc. |
| Non-root container | Docker image runs as user `ingestx` (uid 10001) |
| TLS termination | Caddy with automatic Let's Encrypt |
| Webhook auth | HMAC-SHA256 signature on every ingest request |
| Dashboard auth | `X-Stream-Token` / `WS_AUTH_TOKEN` on ledger + WebSocket |
| Rate limiting | Redis sliding window on ingest endpoint |

---

## Environment reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | Yes | `development` \| `staging` \| `production` |
| `DATABASE_URL` | Yes | `postgresql+psycopg2://...` |
| `REDIS_URL` | Yes | `redis://...` |
| `WEBHOOK_SECRET` | Yes | HMAC secret shared with payment gateway |
| `WS_AUTH_TOKEN` | Yes | Dashboard + ledger API auth |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `API_WORKERS` | No | Uvicorn worker processes (default: 2) |
| `LOG_LEVEL` | No | `info`, `warning`, `error` |

---

## CI/CD extension

The repo includes GitHub Actions for test + build. To add deploy-on-tag:

```yaml
# .github/workflows/deploy.yml (example)
on:
  push:
    tags: ["v*"]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/ingestx && git pull
            docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

---

## Troubleshooting

**App won't start in production**
→ Check logs for `WEBHOOK_SECRET must be set to a secure value`

**`/ready` returns 503**
→ Postgres or Redis not reachable; verify `DATABASE_URL` / `REDIS_URL`

**WebSocket won't connect**
→ Ensure reverse proxy supports WebSocket upgrade (Caddy config included)

**CORS errors on dashboard**
→ `CORS_ORIGINS` must exactly match the browser origin (including `https://`)

**Migrations fail on existing DB**
→ If you used dev `create_all` before, run `alembic stamp 001` then `alembic upgrade head`
