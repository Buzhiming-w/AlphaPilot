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

Project phase: Phase 5 Frontend MVP scaffold.

Completed locally:

- DeepSeek-backed TradingAgents smoke run for `NVDA` on `2024-05-10`.
- Saved reference demo output under `.alphapilot_runtime/`.
- FastAPI backend scaffold with auth, quota, admin controls, and analysis APIs.
- Static frontend workspace under `frontend/`.
- Public demo endpoint backed by the saved smoke result.
- English and Chinese project docs under `docs/`.

Still pending before public deployment:

- Persistent database storage instead of the in-memory MVP store.
- Real background worker for live `TradingAgentsGraph.propagate()` jobs.
- Rate limiting and production-grade session/token handling.
- Deployment documentation and safety checks.
- Browser screenshot verification for the frontend.

## Local Quick Start

Install the project in editable mode:

```bash
pip install -e .
```

Start the backend:

```bash
uvicorn alphapilot.backend.app:app --reload
```

Open the frontend directly:

```text
frontend/index.html
```

The frontend defaults to:

```text
http://127.0.0.1:8000
```

Default local admin account:

```text
admin@alphapilot.dev
admin
```

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

The MVP uses an in-memory repository (`AlphaPilotStore`), so local users and
jobs reset when the backend process restarts.

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
