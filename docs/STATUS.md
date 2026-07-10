# AlphaPilot Status

Last updated: 2026-06-28

## Current Phase

Phase 7: Workflow Router Lean MVP

## Current Task

Fix and deploy the bilingual report pipeline so English is the canonical source report and Chinese is a cached full-report localization.

## Next Steps

1. Verify newly generated live reports produce English source reports and cached Chinese full reports.
2. Continue product testing on the deployed Copilot draft refinement flow.
3. Add browser screenshot verification for the redesigned frontend when browser tooling is available.
4. Add domain/HTTPS when a domain is purchased and DNS points to the server.

## Current Blockers

- Browser screenshot verification is still pending for the latest redesign.
- No domain name yet, so the public demo remains HTTP-only at the server IP.

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
- Deployed Phase 7 to the Alibaba Cloud demo at commit `00a86d8`.
- Public smoke checks passed: `/` returned HTTP 200 and contains Copilot UI, `/health` returned HTTP 200, `/demo/reference` returned HTTP 200, and guest `/copilot/route`, `/watchlist`, and `/compare/test` returned HTTP 401.
- Product review found the Dashboard top-right quick analysis form is a leftover MVP entry point. It should be removed so Dashboard analysis starts from Copilot confirmation or the `Analysis` section.
- Product navigation decision: left sidebar should contain only `Dashboard`, `Analysis`, and `Compare`; `New Analysis` and `Report Detail` merge into `Analysis`; `Watchlist` is hidden as a primary entry; `Login` / account and admin controls move to the top-right area.
- Account area decision: after login, the top-right account area must display the user's `display_name`, with email as fallback.
- `Analysis` and `Compare` must both keep history records, and Dashboard Copilot confirmations should load the matching analysis interface directly.
- Dashboard decision display issue: the saved NVDA demo `Overweight` rating should not appear as the current decision. It should be removed, replaced with `No active analysis`, or relabeled as `Demo result`.
- Copilot UX decision: replace shortcut/action buttons with a two-step conversation flow: one natural-language submit action, then one final confirmation action after the server-side LLM returns a structured draft. Users can correct the draft through the same conversation before confirmation.
- Running report UX decision: `Analysis` and `Compare` should show real workflow progress and interim stage conclusions with a typewriter-style reveal. The backend should emit structured progress events, and the final persisted report should replace or reconcile streamed in-progress text.
- Implemented the Dashboard / Analysis / Compare cleanup locally: removed legacy sidebar items and top-right quick analysis, moved login/account/admin controls to the top-right account area, hid Watchlist from primary navigation, and merged analysis creation/detail/history into `Analysis`.
- Updated Copilot routing to return `analysis` or `compare` drafts, with optional server-side LLM interpretation using the configured Copilot model and deterministic ticker validation fallback.
- Added `analysis_progress_events` persistence, `GET /analysis/{job_id}/progress`, worker progress events, and frontend polling/typewriter display for running reports.
- Fixed live worker result persistence by converting LangChain/TradingAgents raw state into JSON-safe values before writing to database JSON fields.
- Extended Copilot fuzzy discovery so vague requests such as large-cap US healthcare stock research can return candidate tickers for user confirmation.
- Added deletion support for `Analysis` and `Compare` history items, including queued/running/completed analysis jobs; deleted queued jobs are skipped safely if a stale queue entry reaches the worker.
- Latest targeted local test run for router/deletion/frontend checks: `26 passed`.
- Latest full local test run: `359 passed, 9 warnings, 75 subtests passed`.
- Deployed the latest Dashboard / Analysis / Compare redesign to the Alibaba Cloud demo at `http://47.250.149.226/`.
- Ran production migration `20260615_0003_add_analysis_progress_events` on PostgreSQL.
- Rebuilt and restarted production `api`, `worker`, and `caddy` services.
- Public smoke checks passed: `/`, `/health`, and `/demo/reference` returned HTTP 200.
- Production Copilot smoke returned candidate healthcare tickers `LLY`, `UNH`, and `JNJ` for a fuzzy Chinese request.
- Production delete smoke passed: queued `Analysis` job deletion returned HTTP 204 and subsequent detail lookup returned HTTP 404; `Compare` deletion returned HTTP 204.
- Fixed a production SQLAlchemy warning during compare workflow deletion by switching compare symbol cleanup to a bulk delete before deleting the workflow.
- Product UX decision: `Analysis` and `Compare` should treat manual form submission as a secondary path. Dashboard Copilot confirmation should start or create the workflow first, then navigate into the matching workspace without requiring a second `Start Workflow` click.
- Implemented collapsed manual entry points: the `Analysis` form now lives under a closed `Manual analysis` section, and the `Compare` form now lives under a closed `Manual compare` section.
- Latest frontend-focused verification for the collapsed manual sections passed: `pytest -q tests/test_alphapilot_frontend_mvp.py` returned `3 passed`.
- Latest full local test run after the collapsed manual entry update: `359 passed, 9 warnings, 75 subtests passed`.
- Deployed the collapsed manual entry frontend/docs update to `http://47.250.149.226/`.
- Production smoke checks passed for the collapsed manual entry update: `/` contains `Manual analysis` and `Manual compare`, `/styles.css` contains `.manual-workflow`, and `/health` returned `{"status":"ok"}`.
- Product implementation update: Dashboard runtime now binds to selected analysis result/runtime metadata when available, with `--` reserved for jobs that do not expose runtime data.
- Product implementation update: `Analysis` and `Compare` progress panels now include live status headers, elapsed/latest-update labels, liveness indicators, and stage-based progress tracks.
- Product implementation update: final reports now render through a safe Markdown path that escapes raw HTML before producing headings, lists, tables, blockquotes, and code blocks.
- Product implementation update: global `EN` / `中文` UI state is wired into the top-right account area, and report language controls default to English independently of the UI language.
- Product implementation update: the visible Dashboard eyebrow is now `Agentic stock research terminal`, and the left brand no longer shows the small `Research terminal` secondary line.
- Product implementation update: regular users remain limited to 3 live workflows per day, while admin users bypass daily quota and still pass through the existing system-level rate limiter.
- Product implementation update: logged-in users now see a display-name label plus explicit `Logout`; admin users see `Manage Users`, which opens the user management interface.
- Product implementation update: Dashboard now includes a compact `How to use AlphaPilot` guide, with admin-only `Admin tools` guidance.
- Report localization implementation update: when `ALPHAPILOT_REPORT_TRANSLATION_ENABLED=true`, the worker generates a cached Chinese report from the completed English source report, records translation status in `report_translations.zh`, retries failures up to the configured attempt limit, and avoids regenerating when a Chinese report is already cached. English remains the canonical source report.
- Report localization correction: the source workflow output must be generated with `TRADINGAGENTS_OUTPUT_LANGUAGE=English`. The worker now treats the assembled English report as the canonical source, caches the Chinese full-report localization under `localized_sections.zh.report`, and the frontend uses `localized_sections.zh.final` only as a fallback for older results.
- Security Master planning update: added `docs/SECURITY_MASTER_PLAN.md` and Chinese mirror with a database-backed plan for US stock/ETF resolution, Nasdaq Trader + SEC sync, `securities` and `security_aliases` tables, unresolved query logging, and admin-maintained Chinese/person aliases. The design explicitly keeps common Chinese names and person clues in database aliases instead of hardcoded Python lists, and schedules production sync every Monday at 00:00 server time after the first manual sync.
- Security Master implementation update: added Security Master SQLAlchemy models and Alembic migration `20260615_0004_add_security_master_tables`, fixture-backed Nasdaq Trader + SEC sync, seed aliases for common US names/Chinese names/person clues, `SecurityMasterResolver`, app-level resolver wiring, mixed Chinese/English ticker token extraction, month-date parsing for requests such as `2015年6月至今`, and worker-side Monday 00:00 automatic sync scheduling behind `ALPHAPILOT_SECURITY_MASTER_AUTO_SYNC_ENABLED`.
- Product decision: do not build Admin alias-maintenance UI/endpoints in the current phase. For the current single-operator demo, maintain Chinese names, person clues, and other aliases directly in the `security_aliases` database table.
- Next Copilot UX decision: improve draft refinement before adding admin alias UI. Resolved stocks should render as removable chips; ambiguous entities should require user selection; unresolved entities should be shown separately; `Compare` confirmation should require 2 to 5 final selected stocks; `Analysis` confirmation should allow 1 or more selected stocks.
- Copilot draft refinement implementation update: `/copilot/route` now returns candidate groups and unresolved entities; the Dashboard draft renders selected stocks as removable chips, lets users choose among ambiguous ticker candidates, blocks confirmation until unresolved entities are clarified, validates `Compare` at 2 to 5 selected stocks, and validates `Analysis` at 1 or more selected stocks. The local fallback ticker directory now includes common MMM/3M and ORCL/Oracle aliases.
- Deployment update: the Copilot draft refinement update has been deployed to `http://47.250.149.226/`. Production smoke checks passed for `/health`, frontend `/` and `/app.js`, the `比较3M和orcl两只股票的表现，从2015年6月至今` Copilot route, unresolved-entity handling for `Neverland Robotics`, and Docker Compose service health.

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

- 2026-06-15 report translation and Security Master implementation has been deployed to production.
- Verification completed so far: `node --check frontend/app.js`; `pytest -q tests/test_alphapilot_frontend_mvp.py tests/test_alphapilot_backend_mvp.py::test_admin_analysis_creation_bypasses_daily_quota`; and `pytest -q tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_frontend_mvp.py tests/test_alphapilot_phase6.py tests/test_alphapilot_workflow_router.py tests/test_alphapilot_sqlalchemy_store.py`.
- Full local verification completed: `node --check frontend/app.js && pytest -q` returned `360 passed, 9 warnings, 75 subtests passed`.
- Deployed this product feedback pass to `http://47.250.149.226/` by rsyncing the local workspace to `/opt/AlphaPilot`, rebuilding `api` and `worker`, running `alembic upgrade head`, and restarting `api`, `worker`, and `caddy`.
- Production smoke checks passed: `/health` returned `{"status":"ok"}`, `/` contains `Agentic stock research terminal`, `How to use AlphaPilot`, `Manage Users`, and `Logout`, `/app.js` contains `renderMarkdown`, `renderProgressChrome`, `Admin access`, and `alphapilot_ui_locale`, and `api`, `caddy`, `postgres`, `redis`, and `worker` are running.
- Browser screenshot verification is still pending because the in-app browser reported `Browser is not available: iab`; HTTP smoke checks against local `127.0.0.1:4173` and `127.0.0.1:8100/health` passed.
- Current targeted verification for report translation and Security Master passed: `pytest -q tests/test_alphapilot_phase6.py tests/test_alphapilot_security_master.py tests/test_alphapilot_sqlalchemy_store.py tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_workflow_router.py` returned `42 passed`.
- Full local verification after report translation and Security Master changes passed: `node --check frontend/app.js`; `python -m compileall -q alphapilot/backend`; `ALPHAPILOT_DATABASE_URL=sqlite:////tmp/alphapilot_alembic_security_master.db alembic upgrade head`; and `pytest -q` returned `367 passed, 9 warnings, 75 subtests passed`.
- Deployed the report translation and Security Master changes to `http://47.250.149.226/`: rsynced local workspace to `/opt/AlphaPilot`, ensured production `.env.production` enables report translation and Security Master auto sync, rebuilt `api` and `worker`, ran Alembic migration `20260615_0004_add_security_master_tables`, and restarted `api`, `worker`, and `caddy`.
- Production smoke checks passed: `/health` returned `{"status":"ok"}`, homepage contains `Agentic stock research terminal`, `How to use AlphaPilot`, `Manage Users`, and `Logout`, Copilot resolved `比较3M和orcl两只股票的表现，从2015年6月至今` to `MMM` and `ORCL` with `start_date=2015-06-01`, and `api`, `caddy`, `postgres`, `redis`, and `worker` are running.
- Deployed the Copilot draft refinement update to `http://47.250.149.226/`: rsynced the local workspace to `/opt/AlphaPilot`, rebuilt `api` and `worker`, ran `alembic upgrade head`, and restarted `api`, `worker`, and `caddy`.
- Production smoke checks passed: `/health` returned `{"status":"ok"}`, `/` contains `Agentic stock research terminal`, `copilotDraft`, and `Manual analysis`, `/app.js` contains `removeDraftSymbol`, `selectDraftCandidate`, `candidate_groups`, and final symbol-count validation messages, Copilot resolved `比较3M和orcl两只股票的表现，从2015年6月至今` to `MMM` and `ORCL` with `start_date=2015-06-01`, Copilot returned `unresolved_entities=["Neverland Robotics"]` for an unresolved compare request, and `api`, `caddy`, `postgres`, `redis`, and `worker` are running.
- Deployed the bilingual report correction to `http://47.250.149.226/`: production `.env.production` now sets `TRADINGAGENTS_OUTPUT_LANGUAGE=English`, `api` and `worker` were rebuilt/restarted, `/health` returned `{"status":"ok"}`, `/app.js` reads `localized_sections.zh.report` before the legacy `localized_sections.zh.final`, and an in-container smoke confirmed the worker translates the full assembled English report into `localized_sections.zh.report`.

- [x] Phase 7 Workflow Router Lean MVP design review.
- [x] Phase 7 Workflow Router local MVP implementation.
- [x] Phase 7 Workflow Router Alibaba Cloud demo deployment.

## Pending

- [x] Run first complete local stock analysis smoke test.
- [x] Document core architecture.
- [x] Define MVP backend/frontend scope.
- [x] Build backend API and permissions.
- [x] Build frontend product UI.
- [x] Deploy controlled public demo.
- [ ] Add domain/HTTPS and browser screenshot verification.
