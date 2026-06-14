# Phase 7 Workflow Router Implementation Plan

Last updated: 2026-06-15

> **For agentic workers:** REQUIRED SUB-SKILL: Use `test-driven-development` for implementation. This repository will execute the plan inline in the current workspace because the project owner asked to keep work in the current project tree.

**Goal:** Build the Lean MVP described in `docs/WORKFLOW_ROUTER_MVP.md`: logged-in Dashboard Copilot routing natural-language requests into Watchlist, Multi-Stock Compare, or Single Stock Analysis drafts.

**Architecture:** Add small backend boundaries before UI work: ticker directory, workflow router, store persistence, and API endpoints. Keep the first router deterministic and testable, with AI fallback represented as an injectable interface rather than a live LLM call. Keep frontend static and dense, matching the current OpenBB-inspired dashboard style.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL/SQLite test compatibility, vanilla HTML/CSS/JavaScript, pytest.

---

## File Map

- Create `alphapilot/backend/ticker_directory.py`: local US equity records, aliases, person clues, and fuzzy lookup.
- Create `alphapilot/backend/workflow_router.py`: parse user text into a structured draft workflow.
- Modify `alphapilot/backend/schemas.py`: request/response models for Copilot, Watchlist, and Compare.
- Modify `alphapilot/backend/store.py`: in-memory dataclasses and methods for watchlist and compare workflows.
- Modify `alphapilot/backend/db_models.py`: SQLAlchemy records for `watchlist_items`, `compare_workflows`, and `compare_workflow_symbols`.
- Modify `alphapilot/backend/sqlalchemy_store.py`: persistent store methods mirroring the in-memory store.
- Modify `alphapilot/backend/app.py`: authenticated API routes for `/copilot/route`, `/watchlist`, and `/compare`.
- Create `alembic/versions/20260615_0002_add_workflow_router_tables.py`: production migration.
- Modify `frontend/index.html`: add Watchlist, Compare, and Dashboard Copilot UI.
- Modify `frontend/app.js`: call new APIs and render draft workflows.
- Modify `frontend/styles.css`: add right-side Copilot and compact financial workflow styles.
- Add tests:
  - `tests/test_alphapilot_ticker_directory.py`
  - `tests/test_alphapilot_workflow_router.py`
  - extend `tests/test_alphapilot_backend_mvp.py`
  - extend `tests/test_alphapilot_sqlalchemy_store.py`
  - extend `tests/test_alphapilot_frontend_mvp.py`
- Update docs:
  - `docs/STATUS.md`
  - `docs/PROJECT_PLAN.md`
  - matching files under `docs/docs_CN/`

## Task 1: Ticker Directory

**Files:**
- Create: `alphapilot/backend/ticker_directory.py`
- Test: `tests/test_alphapilot_ticker_directory.py`

- [ ] **Step 1: Write the failing tests**

Cover exact ticker, company name, alias, Chinese company name, person clue, ambiguous matches, and no match.

Run:

```bash
pytest tests/test_alphapilot_ticker_directory.py -q
```

Expected: fail because `alphapilot.backend.ticker_directory` does not exist.

- [ ] **Step 2: Implement the minimal directory**

Create a `TickerMatch` dataclass and `LocalTickerDirectory.search(query, limit=5)` method. Include initial records for NVDA, AMD, AAPL, MSFT, GOOGL, AMZN, META, TSLA, and BRK.B. Preserve `market`, `exchange`, `currency`, `confidence`, and `match_reason`.

- [ ] **Step 3: Verify green**

Run:

```bash
pytest tests/test_alphapilot_ticker_directory.py -q
```

Expected: all ticker directory tests pass.

## Task 2: Workflow Router

**Files:**
- Create: `alphapilot/backend/workflow_router.py`
- Test: `tests/test_alphapilot_workflow_router.py`

- [ ] **Step 1: Write the failing tests**

Cover these behaviors:
- "帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在" routes to `multi_compare`, resolves NVDA and AMD, and stores `start_date=2024-01-01`.
- "把苹果加入股票池" routes to `add_to_watchlist`.
- "研究英伟达 2024-05-10" routes to `single_analysis` with `end_date=2024-05-10`.
- unknown vague text routes to `clarify`.

Run:

```bash
pytest tests/test_alphapilot_workflow_router.py -q
```

Expected: fail because `workflow_router` does not exist.

- [ ] **Step 2: Implement the minimal router**

Create `WorkflowRouter.route(message, today=None)`. Use deterministic keyword rules for MVP intents, `LocalTickerDirectory` for symbols, and simple date parsing for ISO dates, "2024 年初", "today", "now", and "现在". Return a serializable draft with `intent`, `symbols`, `start_date`, `end_date`, `analysis_anchor`, `requires_confirmation`, and `message`.

- [ ] **Step 3: Verify green**

Run:

```bash
pytest tests/test_alphapilot_workflow_router.py -q
```

Expected: all workflow router tests pass.

## Task 3: Store And Database Persistence

**Files:**
- Modify: `alphapilot/backend/store.py`
- Modify: `alphapilot/backend/db_models.py`
- Modify: `alphapilot/backend/sqlalchemy_store.py`
- Create: `alembic/versions/20260615_0002_add_workflow_router_tables.py`
- Test: `tests/test_alphapilot_sqlalchemy_store.py`

- [ ] **Step 1: Write the failing persistence tests**

Add tests that:
- create, list, and delete a watchlist item for one user;
- prevent another user from deleting that item;
- create a compare workflow with two symbols and persist it across store instances.

Run:

```bash
pytest tests/test_alphapilot_sqlalchemy_store.py -q
```

Expected: fail because watchlist and compare methods do not exist.

- [ ] **Step 2: Implement in-memory and SQLAlchemy stores**

Add dataclasses `WatchlistItem`, `CompareWorkflow`, and `CompareWorkflowSymbol`. Add store methods:
- `create_watchlist_item`
- `list_watchlist_items`
- `delete_watchlist_item`
- `create_compare_workflow`
- `get_compare_workflow`

Add SQLAlchemy records and a matching Alembic migration. Use foreign keys to `users.id` and optional foreign keys to `analysis_jobs.id`.

- [ ] **Step 3: Verify green**

Run:

```bash
pytest tests/test_alphapilot_sqlalchemy_store.py -q
```

Expected: all SQLAlchemy store tests pass.

## Task 4: API Routes

**Files:**
- Modify: `alphapilot/backend/schemas.py`
- Modify: `alphapilot/backend/app.py`
- Test: `tests/test_alphapilot_backend_mvp.py`

- [ ] **Step 1: Write the failing API tests**

Add tests for:
- guest `/copilot/route` returns 401;
- logged-in `/copilot/route` returns a multi-compare draft without consuming quota;
- `/watchlist` add, list, and delete works for the owner;
- `/compare` creates a workflow for two confirmed symbols;
- inactive users cannot create watchlist or compare workflows.

Run:

```bash
pytest tests/test_alphapilot_backend_mvp.py -q
```

Expected: fail because API routes do not exist.

- [ ] **Step 2: Implement API schemas and routes**

Add request/response models and routes:
- `POST /copilot/route`
- `GET /watchlist`
- `POST /watchlist`
- `DELETE /watchlist/{item_id}`
- `POST /compare`
- `GET /compare/{compare_id}`

Use existing `current_user`, `enforce_rate_limit`, and disabled-account checks.

- [ ] **Step 3: Verify green**

Run:

```bash
pytest tests/test_alphapilot_backend_mvp.py -q
```

Expected: all backend MVP tests pass.

## Task 5: Frontend MVP

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Test: `tests/test_alphapilot_frontend_mvp.py`

- [ ] **Step 1: Write the failing structure tests**

Assert the frontend contains:
- `id="copilotForm"`
- `id="copilotMessage"`
- `id="copilotDraft"`
- `data-view="watchlist"`
- `data-view="compare"`
- JavaScript calls to `/copilot/route`, `/watchlist`, and `/compare`.

Run:

```bash
pytest tests/test_alphapilot_frontend_mvp.py -q
```

Expected: fail because UI elements are not present.

- [ ] **Step 2: Implement UI**

Add a right-side Copilot Panel inside Dashboard. Add compact Watchlist and Compare views to the sidebar. Render returned ticker candidates, date range, and confirmation buttons. Keep guest behavior graceful by showing login-required status when authenticated requests fail.

- [ ] **Step 3: Verify green**

Run:

```bash
pytest tests/test_alphapilot_frontend_mvp.py -q
```

Expected: all frontend structure tests pass.

## Task 6: Full Verification And Docs

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/PROJECT_PLAN.md`
- Modify: `docs/docs_CN/STATUS.md`
- Modify: `docs/docs_CN/PROJECT_PLAN.md`

- [ ] **Step 1: Run focused tests**

```bash
pytest tests/test_alphapilot_ticker_directory.py tests/test_alphapilot_workflow_router.py tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_sqlalchemy_store.py tests/test_alphapilot_frontend_mvp.py -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Run full local suite**

```bash
pytest -q
```

Expected: all tests pass locally before cloud deployment.

- [ ] **Step 3: Update docs**

Mark Phase 7 implementation progress in English and Chinese docs, record known limitations, and note that cloud deployment should happen only after local verification.

- [ ] **Step 4: Commit and push**

```bash
git status --short
git add alphapilot frontend tests alembic docs
git commit -m "feat: add workflow router lean mvp"
git push origin alphapilot-mvp
```

Expected: remote branch includes implementation and docs.

## Self-Review

- Spec coverage: The plan covers Copilot routing, ticker discovery, time parsing, Watchlist, Compare, permission gates, persistence, frontend entry points, docs, and local verification.
- Scope control: The plan does not include full persistent chat history, true range analytics, paid access, alerts, or dedicated compare-agent reasoning.
- Type consistency: All backend API and persistence tasks share the same domain terms: `ticker`, `company_name`, `market`, `exchange`, `currency`, `start_date`, `end_date`, and `analysis_anchor`.
- Placeholder scan: No task depends on undefined later work for the Lean MVP.
