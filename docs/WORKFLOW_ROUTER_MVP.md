# AlphaPilot Workflow Router Lean MVP

Last updated: 2026-06-15

## Goal

The Workflow Router Lean MVP upgrades AlphaPilot from a single-stock report tool into a natural-language research workspace.

The first implementation should let a logged-in user type a natural-language request in the Dashboard, have AlphaPilot identify the intended workflow, resolve likely US stock tickers, parse a date or date range, ask for confirmation, and then route the user into Watchlist, Multi-Stock Compare, or Single Stock Analysis.

This feature remains research assistance only. It must not provide financial advice, execute trades, or expose LLM API keys to the frontend.

## Product Decisions

- Use the Dashboard right-side Copilot Panel as the primary Workflow Router UI.
- Restrict the Copilot to logged-in users in the first version. Guests continue to see only the public demo.
- Support US equities first, while preserving `market`, `exchange`, and `currency` fields for future Hong Kong and A-share expansion.
- Use a hybrid ticker resolution strategy:
  - local US equity directory first;
  - AI parsing fallback when local confidence is low;
  - external market-search provider as a future pluggable interface.
- Support natural-language time ranges, but keep the existing TradingAgents call anchored on `end_date` / `as-of date` for the first version.
- Require explicit user confirmation before creating a watchlist item, compare workflow, or analysis job from an AI-parsed request.

## Supported First-Version Intents

- `add_to_watchlist`: add confirmed ticker candidates to the user's watchlist.
- `single_analysis`: create or prefill one stock analysis workflow.
- `multi_compare`: compare two to five confirmed tickers.
- `clarify`: ask a follow-up question when the request is under-specified.
- `unsupported`: explain that the request is outside the current product scope.

Examples:

```text
帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在
```

Expected parsed workflow:

```json
{
  "intent": "multi_compare",
  "symbols": [
    {
      "ticker": "NVDA",
      "company_name": "NVIDIA Corporation",
      "market": "US",
      "exchange": "NASDAQ",
      "currency": "USD",
      "confidence": "high",
      "match_reason": "Matched Jensen Huang / 黄仁勋 to NVIDIA"
    },
    {
      "ticker": "AMD",
      "company_name": "Advanced Micro Devices, Inc.",
      "market": "US",
      "exchange": "NASDAQ",
      "currency": "USD",
      "confidence": "high",
      "match_reason": "Exact ticker match"
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "latest",
  "analysis_anchor": "latest",
  "requires_confirmation": true
}
```

## User Experience

The Dashboard keeps its current data-first workspace layout. A right-side Copilot Panel is added for logged-in users.

The panel contains:

- a natural-language input field;
- suggested example prompts;
- conversation snippets;
- parsed workflow cards;
- candidate ticker confirmation cards;
- date or date-range confirmation;
- action buttons such as `Confirm Compare`, `Add To Watchlist`, `Start Analysis`, and `Edit`.

The Copilot should not immediately run expensive analysis. It first returns a structured draft workflow and asks the user to confirm or edit.

## Watchlist Lean MVP

The first Watchlist implementation should be deliberately small:

- list the current user's watchlist items;
- add confirmed tickers;
- delete watchlist items;
- store an optional user note;
- store the creation source, such as `manual` or `copilot`.

Suggested item fields:

- `id`
- `user_id`
- `ticker`
- `company_name`
- `market`
- `exchange`
- `currency`
- `note`
- `source`
- `last_analysis_job_id`
- `created_at`
- `updated_at`

No grouping, reminders, automatic refresh, or portfolio sizing is required in the first version.

## Multi-Stock Compare Lean MVP

The first Compare implementation should support two to five tickers.

The compare workflow stores:

- confirmed tickers;
- `start_date`;
- `end_date`;
- `analysis_anchor`;
- creation source;
- status;
- linked analysis jobs when created.

The first Compare page can show side-by-side single-stock analysis outputs instead of building a dedicated compare agent immediately. It should include:

- ticker cards;
- job status for each ticker;
- final decision for each completed analysis;
- selected report sections;
- the original date range;
- a simple aggregate summary if available.

True range analytics, return comparison, drawdown, volatility, event timeline, and a dedicated compare agent are deferred.

## Backend Design

New backend boundaries should stay small and testable:

- `ticker_directory`: local company/ticker/alias/person index and fuzzy lookup.
- `workflow_router`: intent, ticker, and time parsing boundary.
- `watchlist` persistence methods and API routes.
- `compare` persistence methods and API routes.
- `copilot` route endpoint that returns a draft workflow.

Likely API endpoints:

```text
POST /copilot/route
GET /watchlist
POST /watchlist
DELETE /watchlist/{item_id}
POST /compare
GET /compare/{compare_id}
```

The first router response should be deterministic enough to test. AI fallback should be isolated behind an interface so tests can inject a fake resolver.

## Data And Persistence

The SQLAlchemy/PostgreSQL model should add tables for:

- `watchlist_items`
- `compare_workflows`
- `compare_workflow_symbols`

The schema should preserve multi-market fields even though only US equities are supported at first.

Existing `analysis_jobs` and `analysis_results` should remain the source for single-stock analysis output. Compare workflows can reference analysis jobs instead of duplicating full reports.

## Permissions And Safety

- Guests cannot call `/copilot/route`, `/watchlist`, or `/compare`.
- Logged-in inactive users cannot create new analysis or compare workflows.
- Existing daily quota rules apply when a confirmed workflow creates analysis jobs.
- AI parsing does not consume analysis quota by itself, but it should be rate-limited.
- The frontend never receives provider API keys.
- The UI must keep the non-advice disclaimer visible.

## Testing Strategy

Local tests should cover:

- ticker directory matching for company names, tickers, aliases, Chinese names, and known people;
- no-match and ambiguous-match behavior;
- workflow intent routing;
- date and date-range parsing;
- guest access rejection for Copilot, Watchlist, and Compare;
- watchlist add/list/delete;
- compare workflow creation with two to five tickers;
- compare creation rejecting unconfirmed or unsupported tickers;
- quota consumption only when analysis jobs are created;
- frontend structure for the right-side Copilot Panel and confirmation states.

Cloud testing should remain a deployment smoke test after local tests pass.

## Out Of Scope For This MVP

- Real multi-market support beyond US equities.
- True range analytics and backtesting.
- Dedicated compare-specific multi-agent reasoning.
- Full persistent chat history.
- Watchlist grouping, alerts, reminders, or scheduled refresh.
- Portfolio sizing or real trading.
- Payment, billing, or account plans.

## Completion Criteria

- A logged-in user can type a natural-language request and receive a structured draft workflow.
- The router can identify at least common US ticker, company, alias, Chinese-name, and person-based examples.
- The user can confirm candidates and create Watchlist, Compare, or Single Analysis workflows.
- Watchlist items are persisted and visible after reload.
- Compare workflows persist confirmed tickers and date range.
- The Dashboard contains a right-side Copilot Panel that does not break the existing workflow.
- Tests cover the router, watchlist, compare, permission, and frontend structure paths.
