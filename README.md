# AlphaPilot

AlphaPilot is a productized AI stock research workspace built on top of
[TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents).

The current MVP wraps the TradingAgents multi-agent research engine with a
controlled backend and an OpenBB-inspired dashboard so a user can view a saved
demo analysis, register/login locally, submit demo analysis jobs, and inspect
structured analyst reports without exposing server-side LLM API keys.

AlphaPilot is for investment research assistance, portfolio demonstration, and
interview discussion only. It is not financial advice and it does not execute
real trades.

## Current Status

Project phase: Phase 6 Deployment and Safety.

Completed locally:

- DeepSeek-backed TradingAgents smoke run for `NVDA` on `2024-05-10`.
- Saved reference demo output under `.alphapilot_runtime/`.
- FastAPI backend scaffold with auth, quota, admin controls, and analysis APIs.
- SQLAlchemy 2.0 persistence boundary with PostgreSQL-ready migrations.
- Redis-backed background job path for live analysis workers.
- Rate limiting hooks for public demo, auth, and analysis creation endpoints.
- Static frontend workspace under `frontend/`.
- Public demo endpoint backed by the saved smoke result.
- Single-server Docker Compose deployment scaffold with Caddy, API, worker, PostgreSQL, and Redis.
- English and Chinese project docs under `docs/`.

Still pending before real public deployment:

- Purchasing/configuring the Alibaba Cloud lightweight server.
- Filling real `.env.production` secrets on the server.
- Running deployment verification against the real server IP/domain.
- Browser screenshot verification for the frontend.

## Local Quick Start

Install the project in editable mode:

```bash
pip install -e .
```

Start local PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Set the database URL:

```bash
export ALPHAPILOT_DATABASE_URL=postgresql+psycopg://alphapilot:alphapilot@localhost:5432/alphapilot
export ALPHAPILOT_REDIS_URL=redis://localhost:6379/0
```

Run migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn alphapilot.backend.app:app --reload
```

Open the frontend directly:

```text
frontend/index.html
```

The frontend defaults to same-origin API calls for deployment. For direct local file usage, override the API base once in the browser console:

```js
localStorage.setItem("alphapilot_api_base", "http://127.0.0.1:8000")
```

Default local admin account:

```text
admin@alphapilot.dev
admin
```

If `ALPHAPILOT_DATABASE_URL` is unset, the API falls back to the in-memory MVP
store so imports and tests remain lightweight.

## Backend API

Implemented MVP endpoints:

- `GET /health`
- `GET /demo/reference`
- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `POST /analysis`
- `GET /analysis`
- `GET /analysis/{job_id}`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}`

The development path uses SQLAlchemy 2.0 with PostgreSQL. The API can still use
the in-memory `AlphaPilotStore` fallback when no database URL is configured.

Live analysis requests are queued for a background worker in Phase 6. Demo
analysis still completes synchronously from the saved reference output.

## Deployment

The first deployment target is one 2 vCPU / 2 GB Alibaba Cloud lightweight
application server using Docker Compose:

- Caddy for HTTP/HTTPS and static frontend serving.
- FastAPI/Uvicorn for the API.
- PostgreSQL for persistence.
- Redis for queue and rate-limit state.
- One worker process for live TradingAgents jobs.

See `docs/DEPLOYMENT.md` and `.env.production.example`. Codex should pause and
ask for server IP, SSH access, domain, and production secret values before
running real server deployment steps.

## Demo Data

The public demo is based on a successful local DeepSeek run:

- Ticker: `NVDA`
- Trade date: `2024-05-10`
- Selected analyst: `market`
- Final processed decision: `Overweight`

Runtime outputs are stored under `.alphapilot_runtime/`, which is intentionally
ignored by git because it can contain large generated files and local analysis
artifacts.

## Project Docs

The project uses repository docs as persistent planning memory:

- `docs/STATUS.md`
- `docs/PROJECT_PLAN.md`
- `docs/MVP_SCOPE.md`
- `docs/ARCHITECTURE_NOTES.md`
- `docs/DECISIONS.md`

Chinese mirrors are maintained under:

- `docs/docs_CN/`

## Development Verification

Run the test suite:

```bash
pytest -q
```

Focused MVP tests:

```bash
pytest tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_frontend_mvp.py -q
```

## Repository Safety

Do not commit:

- `.env`
- `.alphapilot_runtime/`
- local caches such as `__pycache__/` and `.pytest_cache/`

The frontend never calls LLM providers directly. Live analysis must go through
the backend so API keys remain server-side.

## Attribution

AlphaPilot is based on the open-source
[TradingAgents](https://github.com/TauricResearch/TradingAgents) framework by
TauricResearch. The original engine and upstream research framework remain the
foundation of AlphaPilot's analysis pipeline.
