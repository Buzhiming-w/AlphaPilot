# AlphaPilot Status

Last updated: 2026-06-14

## Current Phase

Phase 6: Deployment And Safety

## Current Task

Phase 6 code and deployment scaffold are in place. Real server deployment is paused until the Alibaba Cloud server, SSH, domain, and production secret values are available.

## Next Steps

1. Buy/configure the Alibaba Cloud lightweight application server.
2. Fill `.env.production` on the server with real secrets and database password.
3. Run production migrations and Docker Compose deployment on the server.
4. Verify the live public URL, Caddy routing, worker processing, rate limiting, and admin controls.
5. Add browser screenshot verification after the public or local deployment URL is available.

## Current Blockers

Waiting for user-provided server details before real deployment:
- Alibaba Cloud server public IP.
- SSH username/authentication method.
- Domain name, if HTTPS with a real hostname is desired.
- Production secret values, especially `DEEPSEEK_API_KEY` and database password.

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

## In Progress

- [ ] Deploy to Alibaba Cloud lightweight server after user provides server details.

## Pending

- [x] Run first complete local stock analysis smoke test.
- [x] Document core architecture.
- [x] Define MVP backend/frontend scope.
- [x] Build backend API and permissions.
- [x] Build frontend product UI.
- [ ] Deploy controlled public demo.
