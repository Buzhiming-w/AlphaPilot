# AlphaPilot Status

Last updated: 2026-06-10

## Current Phase

Phase 5: Frontend MVP

## Current Task

Turn the first backend/frontend MVP scaffold into a connected, persistent product demo.

## Next Steps

1. Replace `AlphaPilotStore` in-memory storage with PostgreSQL/SQLAlchemy or SQLModel.
2. Add a real background worker for live `TradingAgentsGraph.propagate()` runs.
3. Choose the first deployment target and add environment/deployment docs.
4. Add rate limiting and production-grade token/session handling.
5. Add browser screenshot verification once the in-app browser or Playwright runtime is available.

## Current Blockers

None recorded.

## Important Context

- Repository path: `/Users/buzhiming/Desktop/AlphaPilot`
- Current project name: AlphaPilot
- Base project: TauricResearch/TradingAgents
- Local environment name: `AlphaPilot`
- `.env` already contains a DeepSeek API key, but provider/model overrides still need to be verified.
- The original engine entry point is `TradingAgentsGraph.propagate()`.
- Default config currently uses OpenAI unless overridden by `TRADINGAGENTS_*` environment variables.

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
- Full test suite also passed with `pytest -q`: 322 tests and 75 subtests passed, with environment warnings only.

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

## In Progress

- [ ] Replace in-memory store with persistent storage and production background jobs.

## Pending

- [x] Run first complete local stock analysis smoke test.
- [x] Document core architecture.
- [x] Define MVP backend/frontend scope.
- [x] Build backend API and permissions.
- [x] Build frontend product UI.
- [ ] Deploy controlled public demo.
