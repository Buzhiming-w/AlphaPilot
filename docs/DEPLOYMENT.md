# AlphaPilot Deployment

Last updated: 2026-06-14

## Target

The first production deployment targets one Alibaba Cloud lightweight application server:

- 2 vCPU
- 2 GB RAM
- Ubuntu LTS
- Docker Engine and Docker Compose plugin
- One public IPv4 address
- Optional domain name pointed to the server

This is a controlled demo deployment, not a high-traffic production cluster.

## Topology

```text
Internet
  |
  v
Caddy :80/:443
  |-- static frontend from /srv/alphapilot/frontend
  |-- API reverse proxy to FastAPI

FastAPI API
  |-- PostgreSQL
  |-- Redis
  |-- background worker

Worker
  |-- TradingAgentsGraph.propagate()
  |-- PostgreSQL result persistence
  |-- usage and failure logging
```

## Services

- `caddy`: public HTTP/HTTPS entrypoint and static frontend server.
- `api`: FastAPI served by Uvicorn.
- `worker`: background analysis worker.
- `postgres`: persistent product database.
- `redis`: job queue and rate-limit counter storage.

## Required Operator Inputs

Codex should pause and ask the user for these values before real server deployment:

- Alibaba Cloud server public IP.
- SSH username and authentication method.
- Domain name, if HTTPS with a real hostname is desired.
- Production `.env` values, including `DEEPSEEK_API_KEY`.
- Whether to open public registration or require admin-controlled activation.

Current status: deployment code and docs are ready, but real deployment is paused until these values are available.

## Production Environment

Production secrets must be stored in `.env.production` on the server and must not be committed.

Minimum values:

```text
ALPHAPILOT_DATABASE_URL=postgresql+psycopg://alphapilot:<password>@postgres:5432/alphapilot
ALPHAPILOT_REDIS_URL=redis://redis:6379/0
ALPHAPILOT_QUEUE_BACKEND=redis
ALPHAPILOT_RATE_LIMIT_ENABLED=true
ALPHAPILOT_PUBLIC_ORIGIN=https://your-domain.example
DEEPSEEK_API_KEY=<server-only-secret>
TRADINGAGENTS_LLM_PROVIDER=deepseek
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-flash
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro
TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
TRADINGAGENTS_MAX_RISK_ROUNDS=1
```

## Deployment Steps

1. Buy the Alibaba Cloud lightweight application server.
2. Install Docker and the Docker Compose plugin.
3. Clone the AlphaPilot repository on the server.
4. Create `.env.production` from `.env.production.example`.
5. Fill production secrets and database passwords.
6. Point the domain DNS A record to the server IP, if using a domain.
7. Run database migrations.
8. Start the Compose deployment.
9. Verify `/health`, `/demo/reference`, login, admin controls, and disabled-user blocking.

Base commands after the repository and `.env.production` are present:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Health checks:

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/demo/reference
```

Remote commands and DNS-specific checks will be finalized once the server IP, domain, and SSH details are available.

## Safety Checks

Before exposing live analysis publicly:

- Confirm frontend files contain no LLM API keys.
- Confirm disabled users cannot create analysis jobs.
- Confirm rate limiting returns HTTP 429 after configured thresholds.
- Confirm live jobs are queued and completed by the worker.
- Confirm failed worker jobs are marked `failed` and store an error message.
- Confirm `.env.production` is not tracked by git.
