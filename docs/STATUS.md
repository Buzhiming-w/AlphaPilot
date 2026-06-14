# AlphaPilot Status

Last updated: 2026-06-15

## Current Phase

Phase 7: Workflow Router Lean MVP

## Current Task

Finalize and prepare deployment for the locally verified Workflow Router Lean MVP: a logged-in Dashboard Copilot that turns natural-language requests into confirmed Watchlist, Multi-Stock Compare, or Single Stock Analysis workflows.

## Next Steps

1. Commit and push the locally verified Phase 7 MVP.
2. Deploy to the Alibaba Cloud demo only after repository verification is complete.
3. Re-run public smoke checks after deployment.
4. Continue post-Phase-6 hardening after the Workflow Router MVP lands.

## Current Blockers

- No domain name yet, so the first deployment is HTTP-only at the server IP.
- Browser screenshot verification is still pending.
- Workflow Router cloud deployment should wait until local tests pass.

## Important Context

- Repository path: `/Users/buzhiming/Desktop/AlphaPilot`
- Current project name: AlphaPilot
- Base project: TauricResearch/TradingAgents
- Local environment name: `AlphaPilot`
- `.env` already contains a DeepSeek API key, but provider/model overrides still need to be verified.
- The original engine entry point is `TradingAgentsGraph.propagate()`.
- Default config currently uses OpenAI unless overridden by `TRADINGAGENTS_*` environment variables.
- Phase 6 deployment target is a single Alibaba Cloud lightweight application server with 2 vCPU / 2 GB RAM.
- Production topology: Caddy reverse proxy, FastAPI API, static frontend, PostgreSQL, Redis, and a background worker on one Docker Compose host.
- First public deployment URL: `http://47.250.149.226/`
- Server region: Alibaba Cloud Malaysia (Kuala Lumpur), Ubuntu 22.04.
- Server path: `/opt/AlphaPilot`
- Admin credentials were rotated away from the local default. The server-only credentials file is `/root/alphapilot_admin_credentials.txt`.
- Workflow Router Lean MVP design source: `docs/WORKFLOW_ROUTER_MVP.md`.
- Workflow Router constraints: logged-in users only, US equities first, hybrid ticker resolution, user confirmation before workflow execution, and date ranges stored while first analysis remains anchored on `end_date`.

## Recent Notes

- Created project management docs so future work can resume from repository state instead of chat memory.
- Added Chinese mirror docs under `docs/docs_CN/`. Codex should inspect and update the English docs under `docs/` first, then keep the Chinese versions synchronized for user review.
- Started Phase 1 execution: environment/config verification, editable install, and first local analysis run.
- Completed Phase 1 smoke run with `scripts/run_phase1_smoke.py`: `NVDA`, `2024-05-10`, selected analyst `market`, DeepSeek provider, elapsed about 267 seconds, final decision `Overweight`.
- Saved demo output at `.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`.
- Saved full state log at `.alphapilot_runtime/results/NVDA/TradingAgentsStrategy_logs/full_states_log_2024-05-10.json`.
- Found and fixed a market tool registration mismatch: `Market Analyst` prompts for `get_verified_market_snapshot`, but `tools_market` did not register it.
- Added runtime LLM `timeout` / `max_retries` forwarding for explicit config values and covered it with tests.
- Installed the `obra/superpowers` skill set locally for future planning, TDD, debugging, and review workflows. Restart Codex to make the newly installed skills available in the active skill list.
- Completed MVP architecture documentation for the graph flow, agent responsibilities, dataflows, and report sections.
- Added `docs/MVP_SCOPE.md` to freeze roles, quota rules, pages, API endpoints, database concepts, and normalized result shape.
- Added `alphapilot.backend` FastAPI MVP with register/login, `/me`, analysis creation/list/detail, admin user list, and admin user patch routes.
- Added server-side password hashing, bearer-token auth, default daily quota of 3, disabled-user blocking, and demo result loading from the saved NVDA smoke output.
- Added `frontend/` static OpenBB-inspired dashboard workspace with dashboard, new analysis, report detail, admin users, public demo, responsive layout, and visible non-advice disclaimer.
- Added public `GET /demo/reference`, CORS, frontend login/register forms, token persistence, and API-backed analysis submission with demo fallback.
- Verified the new MVP behavior with `pytest tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_frontend_mvp.py -q` passing 8 tests.
- Full test suite also passed with `pytest -q`: 326 tests and 75 subtests passed, with environment warnings only.
- Added SQLAlchemy 2.0 persistence with `SqlAlchemyAlphaPilotStore`, PostgreSQL-ready JSONB fields, token persistence, quota persistence, job/result persistence, and API routes that use repository methods instead of in-memory dictionaries.
- Added Alembic configuration and initial migration for `users`, `user_tokens`, `user_quotas`, `analysis_jobs`, `analysis_results`, and `api_usage_logs`.
- Added `postgres` service to `docker-compose.yml` and `ALPHAPILOT_DATABASE_URL` to `.env.example`.
- Verified the migration with `ALPHAPILOT_DATABASE_URL=sqlite:////tmp/alphapilot_alembic_check.db alembic upgrade head`.
- Re-ran the full test suite after persistence work: `326 passed, 75 subtests passed`.
- Chose Phase 6 deployment design: one Alibaba Cloud lightweight server, Docker Compose, Caddy reverse proxy, PostgreSQL, Redis, FastAPI, static frontend, and one background worker.
- Added Phase 6 background worker path: live analysis jobs are queued by the API and processed outside the HTTP request.
- Added Redis queue implementation, inline test queue, API rate limiting, and worker usage/failure logging.
- Added production deployment scaffold: `docker-compose.prod.yml`, `Caddyfile`, `.env.production.example`, and bilingual `docs/DEPLOYMENT.md`.
- Changed the static frontend to default to same-origin API calls so it works behind Caddy; local direct-file usage can still override `alphapilot_api_base`.
- Verified Phase 6 with `pytest -q`: `332 passed, 75 subtests passed`.
- Verified Alembic migration with SQLite and Docker Compose production config with `.env.production.example`.
- Re-ran tests inside the `AlphaPilot` conda environment after adding the missing `email-validator` dependency required by Pydantic `EmailStr`: `332 passed, 75 subtests passed`.
- Deployed the Docker Compose production stack to `47.250.149.226` with Caddy, FastAPI, PostgreSQL, Redis, and worker services.
- Added a 2 GB swap file on the 2C/2G server for safer image builds.
- Fixed production PostgreSQL admin seeding by flushing users before quota creation.
- Packaged the NVDA demo fixture inside `alphapilot/backend/demo_data/` so `/demo/reference` no longer depends on gitignored `.alphapilot_runtime` files in production.
- Treated Redis queue timeout as an empty queue so the worker stays up while idle.
- Added `ALPHAPILOT_ADMIN_PASSWORD` support and rotated the production admin password to a server-only random value.
- Verified public deployment: `/`, `/health`, and `/demo/reference` return HTTP 200 from `http://47.250.149.226`.
- Verified safety: default `admin` password returns HTTP 401, while the server-only random admin password returns HTTP 200.
- Latest full local test run in the `AlphaPilot` conda environment: `336 passed, 75 subtests passed`.
- Planned Phase 7 Workflow Router Lean MVP: right-side Dashboard Copilot, natural-language intent routing, local-first ticker directory with AI fallback, Watchlist basics, and lightweight Multi-Stock Compare.
- Added `docs/WORKFLOW_ROUTER_MVP.md` and Chinese mirror under `docs/docs_CN/`.
- Added Phase 7 implementation plans in English and Chinese docs; implementation is starting with TDD.
- Added deterministic local ticker directory and Workflow Router MVP boundary with tests for exact ticker, company, Chinese-name, person-clue, date-range, watchlist, single-analysis, and multi-compare routing.
- Added Watchlist and Compare persistence/API/frontend MVP paths, plus Dashboard right-side Copilot Panel.
- Local verification passed: `351 passed, 9 warnings, 75 subtests passed`.
- Verified Alembic migration chain through `20260615_0002_add_workflow_router_tables.py` with SQLite.
- Updated Caddy production proxy rules for Phase 7 API prefixes: `/copilot/*`, `/watchlist*`, and `/compare*`.

## Completed

- [x] Clone base TradingAgents project into AlphaPilot folder.
- [x] Create conda environment named `AlphaPilot`.
- [x] Create `.env` with DeepSeek API key.
- [x] Create project planning documentation.
- [x] Create Chinese mirror documentation under `docs/docs_CN/`.
- [x] Install project into the `AlphaPilot` conda environment with `pip install -e .`.
- [x] Configure `.env` for DeepSeek provider/model overrides.
- [x] Run first DeepSeek-backed local stock analysis smoke test.
- [x] Confirm final decision and logs are produced.
- [x] Document core architecture enough for MVP schema design.
- [x] Define MVP backend/frontend scope.
- [x] Build first backend API/auth/quota/admin scaffold.
- [x] Build first frontend product UI scaffold.
- [x] Add SQLAlchemy/PostgreSQL persistence layer and Alembic migration scaffold.
- [x] Choose first deployment target and Phase 6 production topology.
- [x] Add background worker queue path for live analysis jobs.
- [x] Add rate limiting and production deployment scaffold.
- [x] Deploy controlled public demo to Alibaba Cloud.
- [x] Verify public health/demo endpoints and production worker stability.
- [x] Rotate production admin credentials away from the local default.

## In Progress

- [x] Phase 7 Workflow Router Lean MVP design review.
- [x] Phase 7 Workflow Router local MVP implementation.

## Pending

- [x] Run first complete local stock analysis smoke test.
- [x] Document core architecture.
- [x] Define MVP backend/frontend scope.
- [x] Build backend API and permissions.
- [x] Build frontend product UI.
- [x] Deploy controlled public demo.
- [ ] Add domain/HTTPS and browser screenshot verification.
