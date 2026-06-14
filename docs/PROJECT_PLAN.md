# AlphaPilot Project Plan

Last updated: 2026-06-15

## Goal

AlphaPilot is a productized stock analysis assistant based on TauricResearch/TradingAgents. The first production-style version should let users register, submit US stock analysis jobs, view structured reports, and let an admin control account access and usage quotas to protect the server-side LLM API key.

AlphaPilot is for investment research assistance and interview/demo presentation only. It must not present itself as financial advice or execute real trades.

## Execution Rules

- Update `docs/STATUS.md` before starting a new phase or major task.
- Check off tasks in this file when they are completed.
- Record important technical choices in `docs/DECISIONS.md`.
- Treat the English files under `docs/` as the execution source of truth for Codex.
- Keep the Chinese mirror files under `docs/docs_CN/` synchronized for user review.
- Keep the original TradingAgents engine working before adding product layers around it.
- Do not expose LLM API keys to the frontend.

## Phase 1: Run The Original Engine

Objective: prove the cloned project works locally with DeepSeek before building anything around it.

Status: Completed

Tasks:
- [x] Activate the `AlphaPilot` conda environment.
- [x] Install the package in editable mode with `pip install -e .`.
- [x] Configure `.env` for DeepSeek:
  - `DEEPSEEK_API_KEY`
  - `TRADINGAGENTS_LLM_PROVIDER=deepseek`
  - `TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-flash`
  - `TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro`
  - `TRADINGAGENTS_OUTPUT_LANGUAGE=Chinese`
  - `TRADINGAGENTS_MAX_DEBATE_ROUNDS=1`
  - `TRADINGAGENTS_MAX_RISK_ROUNDS=1`
- [x] Run a minimal stock analysis for `NVDA` or `AAPL`.
- [x] Confirm that a full `final_trade_decision` is produced.
- [x] Confirm that logs/results are written successfully.
- [x] Save one successful output as a reference demo result.

Completion criteria:
- A full local analysis run completes with DeepSeek.
- The final decision and intermediate reports can be inspected.
- Main failure points are known and documented in `docs/STATUS.md`.

Dependencies:
- None.

Must be completed before:
- Backend API wrapper.
- Frontend connected to live analysis.
- Public deployment.

## Phase 2: Understand Core Architecture

Objective: understand the existing engine well enough to safely wrap and modify it.

Status: Completed for MVP

Tasks:
- [x] Read `tradingagents/graph/trading_graph.py`.
- [x] Read `tradingagents/default_config.py`.
- [x] Read `tradingagents/graph/propagation.py`.
- [x] Read `tradingagents/agents/analysts/`.
- [x] Read `tradingagents/agents/researchers/`.
- [x] Read `tradingagents/agents/trader/`.
- [x] Read `tradingagents/agents/risk_mgmt/`.
- [x] Read `tradingagents/agents/managers/portfolio_manager.py`.
- [x] Read `tradingagents/dataflows/`.
- [x] Document the input/output shape of `TradingAgentsGraph.propagate()`.
- [x] Document the final report sections available for the frontend.
- [x] Identify slow, expensive, and failure-prone steps.

Completion criteria:
- `docs/ARCHITECTURE_NOTES.md` explains the agent flow, inputs, outputs, storage, and data sources.
- The backend result schema can be designed from actual engine output rather than guesses.

Dependencies:
- Phase 1 can be done first or in parallel with this reading, but backend implementation should wait until Phase 1 is proven.

Can be parallelized with:
- Frontend visual research.
- Resume/project description drafting.

## Phase 3: Define MVP Product Scope

Objective: freeze a narrow first version that is useful, demoable, and safe.

Status: Completed for MVP

Tasks:
- [x] Define user roles: guest, regular user, admin.
- [x] Define analysis permissions and quotas.
- [x] Define what a public demo user can see without consuming LLM quota.
- [x] Define MVP pages:
  - Login/Register
  - Dashboard
  - New Analysis
  - Analysis Detail
  - Admin Users
  - Public Demo
- [x] Define MVP API endpoints.
- [x] Define database tables.
- [x] Define first deployment target.
- [x] Add visible non-advice disclaimer requirements.

Completion criteria:
- The MVP can be built without scope drift.
- All features protect the server-side LLM key from casual abuse.

Dependencies:
- Phase 1 should be completed.
- Phase 2 should be mostly completed.

Can be parallelized with:
- Static frontend mockups.
- Backend project scaffolding after endpoint/schema decisions are clear.

## Phase 4: Backend MVP

Objective: expose TradingAgents through a controlled backend API.

Status: Completed for Phase 6 scaffold

Recommended stack:
- FastAPI
- SQLAlchemy or SQLModel
- PostgreSQL
- Redis + RQ/Celery/Arq for background jobs
- Pydantic schemas
- Alembic migrations

Tasks:
- [x] Create backend app structure.
- [x] Add configuration loading from environment variables.
- [x] Create database-shaped models:
  - users
  - analysis_jobs
  - analysis_results
  - user_quotas
  - api_usage_logs
- [x] Implement authentication.
- [x] Implement admin user controls.
- [x] Implement usage quota checks.
- [x] Implement background analysis job creation.
- [x] Wrap `TradingAgentsGraph.propagate()` in an engine service.
- [x] Persist raw final state and normalized frontend-friendly result in SQLAlchemy-backed store.
- [x] Add API endpoints:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /me`
  - `POST /analysis`
  - `GET /analysis`
  - `GET /analysis/{job_id}`
  - `GET /admin/users`
  - `PATCH /admin/users/{user_id}`
- [x] Add basic tests for auth, quota, and job creation.

Completion criteria:
- A logged-in user can create an analysis job.
- The job runs in the background.
- The final report can be retrieved by API.
- Admin can disable or limit a user.

Dependencies:
- Phase 1 must be completed.
- Phase 3 API and schema decisions should be completed.

Can be parallelized with:
- Frontend using mocked API responses.
- Deployment research.

## Phase 5: Frontend MVP

Objective: create a polished web experience suitable for interviews and public demos.

Status: Static MVP scaffold implemented

Recommended stack:
- Next.js or Vite React
- TypeScript
- Tailwind CSS
- shadcn/ui or a small local component system

Tasks:
- [x] Create frontend app structure.
- [x] Build auth screens.
- [x] Build dashboard.
- [x] Build new analysis form.
- [x] Build analysis status view.
- [x] Build analysis detail report view.
- [x] Build admin user management view.
- [x] Add public demo page using saved reference output.
- [x] Add non-advice disclaimer in the product.
- [x] Connect frontend to backend API.
- [x] Verify responsive layout primitives with automated file checks.

Completion criteria:
- Users can register, log in, submit analysis, and read results.
- Admin can manage accounts.
- Public demo does not consume LLM quota.
- UI is presentable enough for a portfolio demo.

Dependencies:
- Can start with mocks after Phase 3.
- Live connection requires Phase 4.

Can be parallelized with:
- Backend implementation.
- Resume and README writing.

## Phase 6: Deployment And Safety

Objective: put the app online in a controlled, low-cost, low-abuse way.

Status: Baseline deployment complete

Design:
- Target platform: one 2 vCPU / 2 GB Alibaba Cloud lightweight application server.
- Deployment model: Docker Compose on one host.
- Reverse proxy: Caddy, because it keeps HTTPS and static-file serving simple for a small server.
- Services on the host:
  - Caddy reverse proxy and static frontend.
  - FastAPI API served by Uvicorn.
  - PostgreSQL for product data.
  - Redis for the background job queue and rate limiting counters.
  - One background worker process for live `TradingAgentsGraph.propagate()` jobs.
- Safety defaults:
  - Public visitors can view `GET /demo/reference` without auth.
  - Registered users can create jobs only while active and within quota.
  - Live analysis is queued and processed outside the HTTP request.
  - API keys stay in server-side environment variables and are never exposed to frontend files.
  - Rate limiting applies to public demo, auth, and analysis creation endpoints.
  - Production deployment docs must tell the operator to fill server IP/domain/SSH details outside git.

Tasks:
- [x] Choose deployment providers.
- [x] Configure production environment variable template.
- [x] Set database migrations.
- [x] Configure Redis/background worker.
- [x] Add rate limiting.
- [ ] Add admin-only user activation or invitation flow if needed.
- [x] Add logging for job failures and LLM usage.
- [x] Add deployment README.
- [x] Verify frontend never receives API keys.
- [x] Verify disabled users cannot create jobs.

Completion criteria:
- The site is accessible online.
- A visitor can view public demo content.
- Only permitted users can consume LLM-backed analysis.
- Production secrets are not committed.
- Deployment can be reproduced on a 2 vCPU / 2 GB Alibaba Cloud lightweight server after the operator provides server IP, SSH access, DNS/domain, and secret values.
- Public `/`, `/health`, and `/demo/reference` return HTTP 200.

Dependencies:
- Phase 4 and Phase 5.

## Phase 7: Workflow Router Lean MVP

Objective: turn the Dashboard into a natural-language research workspace that routes logged-in users into Watchlist, Multi-Stock Compare, or Single Stock Analysis workflows.

Status: Local MVP implemented and verified; cloud deployment pending

Design:
- Add a right-side Dashboard Copilot Panel for logged-in users only.
- Parse natural-language requests into a draft workflow.
- Support first-version intents:
  - `add_to_watchlist`
  - `single_analysis`
  - `multi_compare`
  - `clarify`
  - `unsupported`
- Resolve tickers with a hybrid strategy:
  - local US equity directory first;
  - AI fallback when local confidence is low;
  - future external search provider behind an interface.
- Support US equities first while preserving `market`, `exchange`, and `currency` fields for future market expansion.
- Parse natural-language dates and ranges; save `start_date` and `end_date`, but use `end_date` as the first-version TradingAgents analysis anchor.
- Require user confirmation before creating watchlist items, compare workflows, or analysis jobs.

Tasks:
- [x] Choose Lean MVP scope over full workflow platform scope.
- [x] Choose logged-in-only Copilot access.
- [x] Choose US-first implementation with multi-market data fields.
- [x] Choose hybrid ticker resolution.
- [x] Choose date-range storage with `end_date` analysis anchor.
- [x] Write `docs/WORKFLOW_ROUTER_MVP.md` and Chinese mirror.
- [x] Write detailed implementation plan.
- [x] Add ticker directory and resolver tests.
- [x] Add workflow router tests and implementation.
- [x] Add Watchlist persistence, API, tests, and frontend view.
- [x] Add Compare persistence, API, tests, and frontend view.
- [x] Add right-side Dashboard Copilot Panel.
- [x] Verify guest access is blocked for Copilot, Watchlist, and Compare.
- [x] Verify local tests before cloud deployment.
- [ ] Deploy Phase 7 to Alibaba Cloud demo after local verification.

Completion criteria:
- A logged-in user can type a natural-language request and receive a structured draft workflow.
- The router can identify common US tickers, company names, aliases, Chinese names, and person-based examples.
- The user can confirm candidates and create Watchlist, Compare, or Single Analysis workflows.
- Watchlist items persist after reload.
- Compare workflows persist confirmed tickers and date ranges.
- Dashboard contains a right-side Copilot Panel without breaking existing analysis workflows.
- Tests cover router, watchlist, compare, permission, and frontend structure paths.

Dependencies:
- Phase 4 backend API/auth/quota.
- Phase 5 dashboard frontend.
- Phase 6 PostgreSQL/Redis deployment foundation.

Can be parallelized with:
- Documentation polish.
- Domain/HTTPS deployment hardening after the local implementation is stable.

## Phase 8: Portfolio Polish

Objective: turn AlphaPilot into a strong resume and interview project.

Status: Not started

Tasks:
- [ ] Write project README.
- [ ] Add architecture diagram.
- [ ] Add screenshots.
- [ ] Add demo account or demo-only mode.
- [ ] Add cost-control explanation.
- [ ] Add security/abuse-prevention explanation.
- [ ] Add limitations and disclaimer.
- [ ] Write resume bullet points.
- [ ] Prepare interview explanation:
  - problem
  - architecture
  - agent workflow
  - product tradeoffs
  - security decisions
  - deployment decisions

Completion criteria:
- A reviewer can understand the project quickly.
- The project clearly demonstrates full-stack engineering, AI integration, product thinking, and deployment awareness.

Dependencies:
- Can begin once MVP shape is clear.
- Final polish depends on deployed app.

## Optional Enhancements

These should wait until the MVP is working:

- [x] Watchlist promoted into Phase 7.
- [ ] Full persistent chat history.
- [ ] Dedicated compare-specific multi-agent reasoning.
- [ ] Saved portfolios.
- [ ] Analysis comparison across dates.
- [ ] Cost and token usage dashboard.
- [ ] Strategy modes: conservative, balanced, aggressive, long-term, short-term.
- [ ] Earnings calendar integration.
- [ ] Macro event timeline.
- [ ] Backtesting summary.
- [ ] Prompt/admin configuration panel.
- [ ] Email notifications when analysis completes.
- [ ] Payment or invite-code access control.

## Parallelization Map

Strictly serial:
- Phase 1 before live backend wrapper.
- Engine output understanding before final result schema.
- Auth/quota before public live analysis.
- Backend API before frontend live integration.
- Safety checks before deployment.

Can run in parallel:
- Phase 2 code reading and frontend design exploration.
- Phase 3 product scope and static frontend mocks.
- Phase 4 backend and Phase 5 frontend with mocked API.
- Phase 6 deployment preparation and Phase 7 documentation.
