# AlphaPilot MVP Scope

Last updated: 2026-06-10

## Product Boundary

AlphaPilot MVP is a controlled research workspace around the TradingAgents engine. It supports:

- Public visitors viewing a saved NVDA demo result without consuming LLM quota.
- Registered users creating analysis jobs through the backend.
- Admin users enabling/disabling accounts and changing daily quota.
- A financial-dashboard frontend that presents job status, analyst output, debate sections, and final decision.

AlphaPilot does not execute trades, does not provide financial advice, and does not expose LLM API keys to the browser.

## Roles

- Guest: can view public demo content only.
- User: can register, log in, view own quota, create analysis jobs, list own jobs, and view own reports.
- Admin: can do everything a user can do, list all users, disable accounts, and adjust daily limits.

## Quotas And Permissions

- Default daily analysis limit: 3 jobs per user.
- Disabled users cannot create analysis jobs.
- Quota is checked server-side before analysis creation.
- Public demo uses saved output and should not require authentication in the final deployed product.

## MVP Pages

- Login/Register
- Dashboard
- New Analysis
- Analysis Detail
- Admin Users
- Public Demo

The first frontend implementation is a static OpenBB-inspired research workspace under `frontend/`, with dense panels, a command bar, metrics, report panes, user controls, and visible disclaimer copy.

## MVP API Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `POST /analysis`
- `GET /analysis`
- `GET /analysis/{job_id}`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}`
- `GET /demo/reference`

## Data Model

The MVP backend currently uses an in-memory repository with database-shaped entities. The production database should preserve these concepts:

- `users`: email, password hash, display name, role, active flag.
- `analysis_jobs`: owner, ticker, trade date, mode, selected analysts, status, result id, error, timestamps.
- `analysis_results`: job id, normalized frontend result, raw engine state.
- `user_quotas`: user id, daily limit, used today, usage date.
- `api_usage_logs`: future table for request, token, and cost tracking.

## Result Schema

The frontend-friendly result shape is:

```json
{
  "ticker": "NVDA",
  "trade_date": "2024-05-10",
  "decision": "Overweight",
  "sections": {
    "market": "...",
    "investment": "...",
    "trader": "...",
    "final": "..."
  },
  "debates": {
    "investment": {},
    "risk": {}
  }
}
```

The normalizer accepts both `trader_investment_plan` from live graph state and `trader_investment_decision` from persisted log JSON.

## OpenBB-Inspired UI Direction

OpenBB positions itself as a financial data platform for analysts, quants, and AI agents. AlphaPilot should borrow that workspace feel: dense research panels, data-first navigation, command/search controls, analyst output panes, status and quota surfaces, and sober financial-product language.

## First Deployment Target

Not finalized. Recommended next decision: deploy the FastAPI API and static frontend together for the first demo, then split frontend hosting only after database, worker, and rate limiting are in place.
