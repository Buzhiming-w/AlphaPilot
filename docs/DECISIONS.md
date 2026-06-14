# AlphaPilot Decisions

Last updated: 2026-06-15

This document records important technical and product decisions so the project stays understandable over time.

## Decision Log

### 2026-06-10: Keep TradingAgents As The Core Engine

Decision:
- AlphaPilot will not rewrite the TradingAgents multi-agent engine at the beginning.
- The first product version will wrap `TradingAgentsGraph.propagate()` with backend APIs, permissions, background jobs, and frontend views.

Reasoning:
- The original project already contains the main agent workflow.
- Productizing first gives a stronger interview/demo project faster.
- Rewriting the engine before understanding it would add risk without immediate product value.

Consequences:
- Early work should focus on running, understanding, wrapping, and presenting the engine.
- Engine modifications should be incremental and documented.

### 2026-06-10: Protect LLM API Keys On The Server

Decision:
- DeepSeek and any future LLM API keys must remain server-side.
- The frontend must never call LLM providers directly.

Reasoning:
- The user wants public website access without exposing or abusing personal LLM API keys.
- Backend permissions, quotas, and admin controls are required before public live analysis.

Consequences:
- Live analysis must go through the backend.
- Public demo content should use saved sample results unless a user is authorized.

### 2026-06-10: Use Project Docs As Persistent Memory

Decision:
- Project planning, current status, architecture notes, and decisions will be stored in `docs/`.

Reasoning:
- Chat context can become long or compressed.
- Repository docs provide durable project memory.
- These docs can later support README, resume, and interview preparation.

Consequences:
- Future work should start by reading `docs/STATUS.md` and `docs/PROJECT_PLAN.md`.
- Major changes should update these files.

### 2026-06-10: Maintain English Source Docs With Chinese Mirrors

Decision:
- The English files directly under `docs/` are the execution source of truth for Codex.
- The Chinese files under `docs/docs_CN/` are synchronized mirrors for user review and bilingual comparison.

Reasoning:
- Codex generally follows English task wording and technical plans more reliably.
- The user is a native Chinese speaker and benefits from Chinese project management docs.
- Keeping both versions makes execution precise while keeping the project easy for the user to audit.

Consequences:
- Future documentation updates should first update the English source file, then update the corresponding Chinese mirror.
- When resuming project work, Codex should inspect `docs/STATUS.md` and `docs/PROJECT_PLAN.md`; the user can inspect the paired files under `docs/docs_CN/`.

### 2026-06-10: Store Local Runtime Outputs In Workspace-Ignored Directory

Decision:
- AlphaPilot local analysis outputs, cache files, memory logs, and demo smoke outputs should be written under `.alphapilot_runtime/`.
- `.alphapilot_runtime/` is ignored by git.

Reasoning:
- The original TradingAgents default writes under the user's home directory.
- Keeping runtime files in the workspace makes inspection and demo extraction easier.
- Ignoring the directory prevents large/generated analysis artifacts from entering version control.

Consequences:
- `.env` includes `TRADINGAGENTS_RESULTS_DIR`, `TRADINGAGENTS_CACHE_DIR`, and `TRADINGAGENTS_MEMORY_LOG_PATH`.
- Future scripts should place temporary/demo outputs under `.alphapilot_runtime/`.

### 2026-06-10: Add Explicit LLM Runtime Limits For Development Runs

Decision:
- `TradingAgentsGraph._get_provider_kwargs()` now forwards `timeout` and `max_retries` when they are explicitly present in config.
- Defaults remain unchanged.

Reasoning:
- Phase 1 debugging showed that long agent runs need controllable request behavior.
- Background jobs in the future product will also need bounded runtime behavior.

Consequences:
- Smoke/development scripts can set `config["timeout"]` and `config["max_retries"]`.
- Production backend can later expose safe internal runtime limits without changing LLM client code again.

### 2026-06-10: Use Superpowers Skills As A Supporting Workflow

Decision:
- Install the `obra/superpowers` skill set locally and use it as a supporting workflow for AlphaPilot planning, implementation, debugging, TDD, and review.

Reasoning:
- AlphaPilot is becoming a multi-phase product project, so stronger process discipline is useful.
- Superpowers provides skills for brainstorming, writing plans, executing plans, systematic debugging, TDD, and code review.

Consequences:
- Restart Codex to make the newly installed skills appear in the active skill list.
- Future implementation work can reference Superpowers workflows where they fit, while `docs/` remains AlphaPilot's project-specific source of truth.

### 2026-06-10: Start Product Layer With FastAPI And Static Workspace MVP

Decision:
- Add an `alphapilot.backend` FastAPI app with auth, quota, admin controls, analysis jobs, result normalization, and an engine-service boundary.
- Use an in-memory repository for the first tested MVP while preserving database-shaped entities.
- Add a static OpenBB-inspired frontend under `frontend/` before choosing Next.js/Vite.

Reasoning:
- The TradingAgents engine is Python, so FastAPI is the shortest safe path to a product API.
- In-memory storage lets the auth/quota/result flow be tested immediately without blocking on database migrations.
- A static frontend is enough to validate information architecture, product copy, report panes, and responsive dashboard styling before adding a JavaScript build pipeline.

Consequences:
- Phase 6 must replace the in-memory store with persistent database storage before public deployment.
- Live engine runs still need a real background worker before production use.
- The frontend can be opened directly from `frontend/index.html` and later migrated into Next.js/Vite if needed.

### 2026-06-10: Normalize Engine Output Before Sending To Frontend

Decision:
- Add `alphapilot/backend/result_normalizer.py` as the stable boundary between raw TradingAgents state/logs and frontend report sections.
- Support both `trader_investment_plan` and `trader_investment_decision`.

Reasoning:
- Live state and persisted log JSON currently use different trader field names.
- The frontend should not know about raw engine naming drift.

Consequences:
- API consumers use stable section names: `market`, `sentiment`, `news`, `fundamentals`, `investment`, `trader`, and `final`.
- Future engine changes should be absorbed in the normalizer when possible.

### 2026-06-14: Use PostgreSQL With SQLAlchemy 2.0 For Product Persistence

Decision:
- Use SQLAlchemy 2.0 as the backend persistence boundary.
- Use PostgreSQL for local development and production through `ALPHAPILOT_DATABASE_URL`.
- Use Alembic for schema migrations.
- Keep the in-memory `AlphaPilotStore` as a fallback for lightweight imports/tests when no database URL is configured.

Reasoning:
- AlphaPilot's core product data is relational: users, tokens, quotas, jobs, results, and usage logs.
- PostgreSQL supports production concurrency and JSONB storage for raw TradingAgents state.
- Developing against PostgreSQL reduces SQLite-to-PostgreSQL drift before deployment.
- SQLAlchemy keeps the API layer independent from database-specific details.

Consequences:
- Developers should start PostgreSQL with `docker compose up -d postgres`, set `ALPHAPILOT_DATABASE_URL`, and run `alembic upgrade head`.
- Tests can still inject temporary SQLite URLs for fast repository verification.
- Background workers should reuse the same SQLAlchemy repository/session pattern.

### 2026-06-14: Deploy Phase 6 On One Alibaba Cloud Lightweight Server With Caddy

Decision:
- The first online AlphaPilot deployment will target one 2 vCPU / 2 GB Alibaba Cloud lightweight application server.
- Docker Compose will run Caddy, FastAPI/Uvicorn, the static frontend, PostgreSQL, Redis, and one background worker on the same host.
- Caddy is the reverse proxy and HTTPS entrypoint.

Reasoning:
- A single lightweight server keeps cost and operations complexity low for the first public demo.
- Docker Compose makes the deployment reproducible and easy to explain in interviews.
- Caddy reduces reverse-proxy and TLS configuration burden compared with a custom Nginx setup.
- The app is low-throughput and quota-controlled, so a single worker is enough for Phase 6.

Consequences:
- Production docs must be explicit about memory limits, swap, secrets, DNS, and operator-provided server details.
- The backend must move live analysis into a worker process before public use.
- The app can later split frontend hosting, managed PostgreSQL, or managed Redis if usage grows.

### 2026-06-14: Use Redis Queue And API Rate Limiting For Deployment Safety

Decision:
- Use Redis for background job dispatch and simple rate-limit counters.
- Keep an inline queue implementation for tests and local fallback.
- Apply rate limits to public demo, auth, and analysis creation endpoints.

Reasoning:
- `TradingAgentsGraph.propagate()` can take minutes and should not block an HTTP request.
- Redis is already available as a small Docker service and fits the 2 GB deployment target better than a heavier task system.
- Rate limiting plus admin quotas reduces casual abuse of server-side LLM keys.

Consequences:
- The API creates queued jobs and returns immediately for live analysis.
- A worker process owns live engine execution and failure logging.
- Tests should cover disabled users, quota exhaustion, queued job creation, worker completion/failure, and rate-limit rejection.

### 2026-06-15: Build Workflow Router As A Lean MVP

Decision:
- Phase 7 will implement the Workflow Router as a Lean MVP rather than a full workflow platform.
- The first version will add a logged-in-only right-side Dashboard Copilot Panel.
- The Copilot will parse natural-language requests into draft workflows and require user confirmation before execution.
- First-version workflows are Watchlist, Multi-Stock Compare, and Single Stock Analysis.
- First-version market support is US equities only, while schema and API shapes preserve `market`, `exchange`, and `currency` fields for future expansion.
- Ticker resolution will use a hybrid strategy: local US equity directory first, AI fallback second, and future external search behind an interface.
- Natural-language date ranges will be parsed and stored, but the existing TradingAgents analysis will continue using `end_date` as the first-version as-of date.

Reasoning:
- The current deployed product is a working single-stock analysis demo; the next highest-value step is turning it into a research workspace.
- A Lean MVP gets the full user journey working sooner: natural-language request, candidate confirmation, and workflow creation.
- Building a full compare-specific agent, persistent chat system, and advanced range analytics immediately would create too much product and implementation risk.

Consequences:
- Implementation must prioritize deterministic, testable router behavior before open-ended chat behavior.
- Watchlist and Compare should start with simple persistence and side-by-side single-stock analysis outputs.
- Full persistent chat history, true range analytics, dedicated compare-agent reasoning, alerts, grouping, and multi-market execution remain out of scope for Phase 7.
- Future implementation work should start from `docs/WORKFLOW_ROUTER_MVP.md`.

## Proposed But Not Final

### Backend Stack

Candidate:
- FastAPI
- PostgreSQL
- SQLAlchemy or SQLModel
- Redis with RQ, Celery, or Arq

Reasoning:
- The engine is Python.
- Analysis jobs may take too long for normal HTTP request/response flow.
- FastAPI is lightweight and strong for portfolio/demo APIs.

Status:
- FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Redis, and a lightweight Redis queue are chosen for the Phase 6 backend.

### Frontend Stack

Candidate:
- React with Next.js or Vite
- TypeScript
- Tailwind CSS
- shadcn/ui or a small custom component system

Reasoning:
- Good for building a polished dashboard quickly.
- Strong ecosystem for auth flows, dashboard layouts, and deployment.

Status:
- Static HTML/CSS/JS chosen for the first MVP workspace. Next.js or Vite can still be adopted after API and storage hardening.

### Access Control Model

Candidate:
- Public visitors can view saved demo results.
- Registered users require activation or strict quota.
- Admin can enable/disable accounts and set daily/monthly analysis limits.

Reasoning:
- Prevents casual abuse of LLM-backed analysis.
- Still allows interviewers to inspect the product.

Status:
- Adopted for MVP with bearer-token auth, default daily quota of 3, and admin enable/disable controls.
