# AlphaPilot Architecture Notes

Last updated: 2026-06-14

This document tracks what we learn while reading the TradingAgents codebase and adapting it into AlphaPilot.

## Current Understanding

AlphaPilot will keep the TradingAgents Python engine as the decision-analysis core and add product layers around it:

- Backend API for authentication, permissions, quotas, and job orchestration.
- Background worker for slow LLM analysis runs.
- Database for users, jobs, results, quotas, and usage logs.
- Frontend for submitting stock analysis and viewing reports.
- Admin controls to prevent abuse of server-side LLM API keys.
- Caddy reverse proxy for the first single-server production deployment.

## Phase 4/5 MVP Implementation Snapshot

Current product-layer files:

- `alphapilot/backend/app.py`: FastAPI app factory and route definitions.
- `alphapilot/backend/store.py`: in-memory repository with database-shaped user, quota, job, and result entities.
- `alphapilot/backend/sqlalchemy_store.py`: SQLAlchemy 2.0 repository for persistent product data.
- `alphapilot/backend/db_models.py`: ORM model definitions for users, tokens, quotas, jobs, results, and usage logs.
- `alembic/`: migration environment and initial schema migration.
- `alphapilot/backend/engine_service.py`: service boundary between API routes and `TradingAgentsGraph`.
- `alphapilot/backend/result_normalizer.py`: converts raw engine state or saved log JSON into frontend result sections.
- `alphapilot/backend/security.py`: local password hashing and bearer-token generation.
- `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`: static OpenBB-inspired MVP workspace.

Persistence direction:

- Local development and deployment should use PostgreSQL through `ALPHAPILOT_DATABASE_URL`.
- SQLAlchemy JSON fields use PostgreSQL `JSONB` when running on PostgreSQL and generic JSON on SQLite/test databases.
- If no `ALPHAPILOT_DATABASE_URL` is set, `create_app()` falls back to the in-memory MVP store so imports and unit tests remain lightweight.
- API routes use repository methods such as `get_job()`, `get_result()`, and `list_users()` instead of reading in-memory dictionaries directly.

Database tables:

- `users`
- `user_tokens`
- `user_quotas`
- `analysis_jobs`
- `analysis_results`
- `api_usage_logs`

## First Verified Local Run

Command:

- `conda run --no-capture-output -n AlphaPilot python scripts/run_phase1_smoke.py`

Run details:

- Ticker: `NVDA`
- Trade date: `2024-05-10`
- Selected analysts: `market`
- LLM provider: `deepseek`
- Quick model: `deepseek-v4-flash`
- Deep model: `deepseek-v4-pro`
- Elapsed time: about 267 seconds
- Final processed decision: `Overweight`

Output files:

- Demo summary: `.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`
- Full state log: `.alphapilot_runtime/results/NVDA/TradingAgentsStrategy_logs/full_states_log_2024-05-10.json`
- Memory log: `.alphapilot_runtime/memory/trading_memory.md`

Observed available sections in the smoke output:

- `market_report`
- `investment_plan`
- `trader_investment_plan`
- `final_trade_decision`

Important finding:

- `Market Analyst` instructs the model to call `get_verified_market_snapshot`, but the graph's `tools_market` node originally only registered `get_stock_data` and `get_indicators`.
- This caused an invalid tool call during the first diagnostic run.
- Fixed by registering `get_verified_market_snapshot` in `TradingAgentsGraph._create_tool_nodes()`.

## Core Engine

Primary class:

- `tradingagents/graph/trading_graph.py`
- `TradingAgentsGraph`

Primary method:

- `TradingAgentsGraph.propagate(company_name, trade_date, asset_type="stock")`

Expected high-level input:

- Ticker symbol, such as `NVDA` or `AAPL`.
- Trade date, such as `2026-06-10`.
- Asset type, usually `stock`.

Verified high-level output:

- Full graph state.
- Processed trading decision signal.

Detailed behavior:

- `TradingAgentsGraph.propagate(company_name, trade_date, asset_type="stock")` runs synchronously and may take minutes.
- It returns `(final_state, processed_signal)`.
- It writes a JSON full-state log under `results_dir/<safe_ticker>/TradingAgentsStrategy_logs/full_states_log_<trade_date>.json`.
- It stores the final decision in the memory log for later reflection.
- If `checkpoint_enabled` is true, it recompiles the graph with a per-ticker/date checkpoint thread and clears the checkpoint after successful completion.

The smoke run verified that the full state log contains:

- `company_of_interest`
- `trade_date`
- `market_report`
- `sentiment_report`
- `news_report`
- `fundamentals_report`
- `investment_debate_state`
- `trader_investment_decision`
- `risk_debate_state`
- `investment_plan`
- `final_trade_decision`

Known naming mismatch:

- Live graph state uses `trader_investment_plan`.
- Persisted full-state log JSON uses `trader_investment_decision`.
- The AlphaPilot backend normalizer accepts both and exposes a stable frontend section called `trader`.

## Agent Flow

The graph is assembled in `tradingagents/graph/setup.py`.

1. Selected analyst nodes run in sequence from the configured list: `market`, `social`, `news`, and/or `fundamentals`.
2. Each analyst can call a matching tool node until the conditional logic sees no further tool call.
3. Analyst messages are cleared before moving to the next analyst to keep state manageable.
4. Bull and bear researchers debate the investment case.
5. The research manager writes `investment_plan`.
6. The trader turns the plan into `trader_investment_plan`.
7. Aggressive, conservative, and neutral risk debators discuss the trader plan.
8. The portfolio manager writes `final_trade_decision`.

## Agent Responsibilities

- Market analyst: technical indicators, OHLCV data, verified market snapshot, and price/indicator interpretation.
- Sentiment analyst: collected ticker news/social-style sentiment inputs.
- News analyst: ticker-specific and macro news via `get_news`, `get_global_news`, and insider transaction tools.
- Fundamentals analyst: company profile, fundamentals, balance sheet, cash flow, and income statement tools.
- Bull researcher: strongest pro-investment case.
- Bear researcher: strongest risk/downside case.
- Research manager: final investment plan after debate.
- Trader: actionable investment decision plan from research.
- Risk debators: aggressive, conservative, and neutral perspectives.
- Portfolio manager: final risk-adjusted decision.

## Dataflows

Current dataflow modules include:

- `y_finance.py`, `stockstats_utils.py`, and `market_data_validator.py` for market and indicator data.
- `yfinance_news.py`, `reddit.py`, and `stocktwits.py` for news/sentiment-style inputs.
- `alpha_vantage_*` modules for optional Alpha Vantage market, news, fundamentals, and indicators.
- `symbol_utils.py` and `config.py` for ticker handling and vendor selection.

Risk areas:

- Network/data-provider instability.
- Recent dates with incomplete market data.
- LLM tool-call mismatch with registered tools.
- Long synchronous runtime if called directly in an HTTP request.

## Current Code Areas To Study

- `tradingagents/default_config.py`
  - Default model/provider configuration.
  - Results/cache paths.
  - Debate rounds and analyst settings.
  - Data vendor configuration.

- `tradingagents/graph/trading_graph.py`
  - Engine orchestration.
  - LLM client setup.
  - Tool node setup.
  - State logging.
  - Checkpoint/resume behavior.

- `tradingagents/graph/propagation.py`
  - Initial graph state shape.
  - Graph invocation args.

- `tradingagents/agents/analysts/`
  - Market analyst.
  - Sentiment/social analyst.
  - News analyst.
  - Fundamentals analyst.

- `tradingagents/agents/researchers/`
  - Bull researcher.
  - Bear researcher.
  - Research manager.

- `tradingagents/agents/trader/`
  - Trader agent and investment plan generation.

- `tradingagents/agents/risk_mgmt/`
  - Aggressive, neutral, and conservative risk discussion.

- `tradingagents/agents/managers/portfolio_manager.py`
  - Final portfolio decision.

- `tradingagents/dataflows/`
  - Market data.
  - News data.
  - Fundamentals data.
  - Ticker handling.

## Report Sections To Expose In Frontend

Confirmed sections based on `TradingAgentsGraph._log_state()` and the NVDA smoke output:

- `market_report`
- `sentiment_report`
- `news_report`
- `fundamentals_report`
- `investment_debate_state`
- `trader_investment_decision`
- `risk_debate_state`
- `investment_plan`
- `final_trade_decision`

AlphaPilot API exposes these as normalized sections:

- `market`
- `sentiment`
- `news`
- `fundamentals`
- `investment`
- `trader`
- `final`

## Product Architecture Draft

```text
User Browser
    |
    v
Frontend App
    |
    v
Backend API
    |
    +--> Auth and permissions
    +--> Quota checks
    +--> Analysis job records
    |
    v
Background Worker
    |
    v
TradingAgentsGraph.propagate()
    |
    +--> LLM provider: DeepSeek
    +--> Market/news/fundamental data providers
    |
    v
Database stores final result
```

## Open Questions

- What exact DeepSeek models should AlphaPilot use for quick and deep thinking?
- How long does one default analysis take?
- What is the average token/API cost per analysis?
- Which analyst modules should be enabled for the public MVP?
- Should regular users be allowed to pick date and depth, or should that be admin-controlled?
- Should signup be open, invite-only, or admin-approved?

## Risks

- LLM cost abuse if analysis creation is public without quotas.
- Slow analysis jobs if run directly inside HTTP requests.
- External data provider instability.
- Non-deterministic LLM output.
- Financial advice liability if product language is careless.
- Deployment complexity if worker/database/cache are added too late.

## Phase 6 Deployment Architecture

The first production deployment targets a single 2 vCPU / 2 GB Alibaba Cloud lightweight application server. The deployment should stay intentionally small:

```text
Internet
  |
  v
Caddy :80/:443
  |-- /api/* and backend routes -> FastAPI/Uvicorn
  |-- static assets -> frontend/

FastAPI
  |-- PostgreSQL: users, tokens, quotas, jobs, results, usage logs
  |-- Redis: queue and rate-limit counters
  |-- Worker: live TradingAgentsGraph.propagate() jobs
```

Live analysis must not run inside the HTTP request path. `POST /analysis` creates a queued job after auth, active-user, quota, and rate-limit checks. A worker loads the job from persistent storage, marks it running, calls the engine service, persists the normalized result/raw state, records usage or failure metadata, and marks the job completed or failed.

## Notes To Fill After First Run

- Real sample command: `conda run --no-capture-output -n AlphaPilot python scripts/run_phase1_smoke.py`
- Real runtime: about 267 seconds for the `market`-only smoke path.
- Real output path: `.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`
- Real final decision shape: processed signal string plus full Markdown-style `final_trade_decision`.
- Failed dependencies or missing keys: none after `.env` DeepSeek settings were added.
- Recommended minimal config: DeepSeek provider/model env vars, workspace runtime paths, and explicit LLM timeout/max_retries for smoke/development runs.
