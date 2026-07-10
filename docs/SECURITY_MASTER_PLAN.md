# Security Master And Entity Resolution Plan

Last updated: 2026-06-15

Implementation status:

- Local implementation now includes the database models, Alembic migration, fixture-backed Nasdaq Trader + SEC sync, initial alias seed, `SecurityMasterResolver`, Copilot router wiring, and worker-side Monday 00:00 auto-sync scheduler.
- Product decision: do not build Admin alias-maintenance UI/endpoints in the current phase. For the current single-operator demo, maintain Chinese names, person clues, and other aliases directly in the `security_aliases` database table.

## Goal

AlphaPilot's Copilot needs a broader and more reliable way to identify stocks, ETFs, and common market proxies from natural-language requests.

The current `LocalTickerDirectory` is intentionally small and deterministic, but it is too narrow for real user input. For example, a request such as:

```text
Compare 3M and ORCL from June 2015 to now.
```

should resolve to:

- `MMM` / 3M Company;
- `ORCL` / Oracle Corporation;
- intent: `compare`;
- start date: `2015-06-01`;
- end date: current date.

The solution should not rely on the LLM as the only source of truth. AlphaPilot should use a local Security Master as the authoritative confirmation layer, while LLM parsing remains a language-understanding helper.

## Product Principle

Use a hybrid entity-resolution model:

```text
User natural language
-> Copilot extracts intent, entities, and dates
-> Security Master resolves and validates securities
-> User confirms candidates
-> AlphaPilot starts Analysis or Compare workflow
```

The LLM may infer that the user mentioned "Oracle" or "3M", but the final ticker must be confirmed through the Security Master.

## Why Not LLM-Only

An LLM-only ticker resolver is risky for a financial research product:

- It can hallucinate ticker symbols.
- It may confuse renamed companies, share classes, ADRs, ETFs, and similarly named issuers.
- It consumes tokens on every lookup.
- It is hard to audit.
- It may return plausible but stale or invalid symbols.

AlphaPilot should use the LLM for semantic extraction, not as the final securities database.

## Why Not Manual-Only

A hand-maintained `ticker_directory.py` does not scale:

- US equities and ETFs contain thousands of active listings.
- Companies rename, merge, split, and delist.
- Users search by ticker, company name, brand, Chinese name, old name, CEO/founder/person clue, and industry phrase.
- Manual hardcoding makes every new miss a code change.

The first scalable version should load official or semi-official market data into PostgreSQL, then maintain aliases in database tables.

## Recommended Data Sources

### 1. Nasdaq Trader Symbol Directory

Purpose:

- Current listed securities across Nasdaq and other US exchanges.
- Useful fields include symbol, security name, exchange, ETF flag, test issue flag, and listing metadata.

Initial files:

- `https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt`
- `https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt`

Use:

- Primary active US listing source.
- Exclude test issues.
- Classify ETF versus non-ETF from the ETF flag.
- Preserve raw source rows for audit/debugging.

### 2. SEC EDGAR Company Tickers

Purpose:

- CIK, ticker, SEC company name, and exchange associations.
- Useful for linking later filings, fundamentals, and 10-K/10-Q workflows.

Initial file:

- `https://www.sec.gov/files/company_tickers_exchange.json`

Use:

- Enrich Security Master records with `cik`.
- Add SEC conformed company names as aliases when they differ from exchange names.
- Do not treat SEC data as a complete active listing source by itself.

### 3. Optional Future Source: Financial Modeling Prep

Purpose:

- Company symbol lists, ETF lists, index lists, profile data, sector/industry metadata, and ETF details.

Use:

- Optional enrichment after the Nasdaq + SEC path is stable.
- Requires API key and review of quota/licensing limits.
- Should not be required for the first Security Master MVP.

### 4. yfinance Usage Boundary

Purpose:

- Price/history/profile validation for a known symbol.

Use:

- Useful as a post-resolution check or data fetcher.
- Not recommended as the authoritative full symbol list.

## Database Model

### `securities`

Stores canonical tradable or researchable instruments.

Suggested fields:

```text
id
symbol
normalized_symbol
name
normalized_name
exchange
market
currency
asset_type
is_etf
cik
status
source
first_seen_at
last_seen_at
delisted_at
raw_payload
created_at
updated_at
```

Field notes:

- `symbol`: canonical display symbol, such as `ORCL`, `MMM`, `SPY`, `BRK.B`.
- `normalized_symbol`: lowercase and punctuation-normalized symbol for search.
- `asset_type`: examples include `stock`, `etf`, `adr`, `preferred`, `warrant`, `unit`, `fund`, `index_proxy`, `unknown`.
- `status`: `active`, `inactive`, `delisted`, or `unknown`.
- `raw_payload`: JSONB snapshot from the source row.

Indexes:

- Unique index on `(market, symbol)`.
- Index on `normalized_symbol`.
- Index on `normalized_name`.
- PostgreSQL trigram index on `normalized_name` and alias values after `pg_trgm` is enabled.

### `security_aliases`

Stores alternate names and user-facing search clues.

Suggested fields:

```text
id
security_id
alias
normalized_alias
alias_type
confidence
source
created_at
updated_at
```

Alias types:

- `company_short_name`
- `company_legal_name`
- `sec_name`
- `old_name`
- `brand`
- `english_common_name`
- `chinese_name`
- `chinese_abbreviation`
- `person`
- `manual`
- `llm_suggested`

Important requirement:

- Common Chinese names and person clues must be maintained in the database, not hardcoded in Python.
- Examples:
  - `甲骨文` -> `ORCL`
  - `3M` -> `MMM`
  - `英伟达` -> `NVDA`
  - `黄仁勋` -> `NVDA`
  - `巴菲特的公司` / `伯克希尔` -> `BRK.B`

Person aliases:

- Store CEO/founder/person clues in `security_aliases` with `alias_type='person'`.
- These aliases should be manually curated first, then extended from failure logs.
- Do not depend on live web search for every request.

### `security_master_sync_runs`

Stores ingestion audit history.

Suggested fields:

```text
id
source
started_at
finished_at
status
inserted_count
updated_count
deactivated_count
error
raw_metadata
```

### `security_resolution_failures`

Stores unresolved or low-confidence Copilot queries for later alias maintenance.

Suggested fields:

```text
id
user_id
query
entities
reason
created_at
resolved_at
resolved_by_user_id
notes
```

Use:

- When Copilot cannot resolve a request, store the failed query.
- Admin can review recurring failures and add aliases without code changes.

## Sync Pipeline

Create a script or CLI command:

```bash
python -m alphapilot.backend.security_master.sync
```

First-version steps:

1. Download `nasdaqlisted.txt`.
2. Download `otherlisted.txt`.
3. Download SEC `company_tickers_exchange.json`.
4. Parse all source records with structured parsers.
5. Normalize symbols, names, exchanges, and asset types.
6. Upsert into `securities`.
7. Upsert source-derived aliases into `security_aliases`.
8. Mark missing previously active records as `inactive` rather than deleting them.
9. Write a `security_master_sync_runs` record.

Local development:

- Run manually.
- Seed a small fixture for tests.

Production:

- Run manually first after deployment.
- Then run automatically every Monday at 00:00 server time.
- Use cron or the existing Docker worker/scheduler, and record every scheduled run in `security_master_sync_runs`.

Failure behavior:

- If one source fails but another succeeds, record partial status and do not wipe existing data.
- Never delete canonical securities during a failed sync.

## Resolver Behavior

Create a resolver boundary, for example:

```text
SecurityMasterResolver.resolve(query, limit=5)
```

Resolution order:

1. Exact symbol match.
2. Exact alias match.
3. Exact normalized company name match.
4. Prefix/contains search on names and aliases.
5. Trigram/fuzzy search.
6. Optional LLM-extracted entity search.

Return shape should include:

```text
ticker
company_name
market
exchange
currency
asset_type
confidence
match_reason
source
```

Confidence guidance:

- `high`: exact symbol, exact alias, exact name.
- `medium`: prefix/contains/fuzzy match with a clear top candidate.
- `low`: ambiguous or weak match.

Workflow behavior:

- High confidence single match can be shown directly in the confirmation draft.
- Multiple or medium/low confidence matches should be shown as candidates for user confirmation.
- No confirmed ticker should start a workflow until the user confirms.

## Copilot Integration

Keep the current Copilot LLM role, but change the validation source.

Current:

```text
LLM optional hint + hardcoded LocalTickerDirectory
```

Target:

```text
LLM optional hint + SecurityMasterResolver backed by PostgreSQL
```

The LLM should extract structured hints:

```json
{
  "intent": "analysis|compare|clarify|unsupported",
  "entities": ["3M", "orcl"],
  "start_date": "2015-06-01",
  "end_date": null
}
```

Then the resolver validates:

```text
3M -> MMM / 3M Company
orcl -> ORCL / Oracle Corporation
```

The LLM should not be allowed to create final ticker truth without Security Master confirmation.

## Admin Maintenance

Do not add admin-only alias maintenance UI/endpoints in the current phase.

For the single-operator demo, maintain aliases directly in PostgreSQL:

- Insert or update rows in `security_aliases`.
- Use `alias_type='chinese_name'`, `alias_type='chinese_abbreviation'`, `alias_type='person'`, `alias_type='old_name'`, or `alias_type='brand'`.
- Keep `source='manual'` for operator-added aliases.
- Keep user confirmation before workflows so a bad alias cannot silently start analysis.

This keeps "common Chinese names / person clues" as operational data rather than Python code, without spending product surface area on an admin UI yet.

First useful admin actions:

- Add `chinese_name`.
- Add `chinese_abbreviation`.
- Add `person`.
- Add `old_name`.
- Add `brand`.

## Initial Alias Seed

The first database seed should include high-value aliases for the most common US large-cap stocks and ETFs.

Examples:

```text
MMM: 3M, 3M Company, 明尼苏达矿务, 3M公司
ORCL: Oracle, Oracle Corporation, 甲骨文
NVDA: NVIDIA, 英伟达, 辉达, 黄仁勋, Jensen Huang
AMD: Advanced Micro Devices, 超威半导体, 苏姿丰, Lisa Su
AAPL: Apple, 苹果, 苹果公司, Tim Cook, 库克
MSFT: Microsoft, 微软, Satya Nadella, 纳德拉
GOOGL/GOOG: Google, Alphabet, 谷歌, 字母表
META: Meta, Facebook, 脸书, Zuckerberg, 扎克伯格
TSLA: Tesla, 特斯拉, Elon Musk, 马斯克
BRK.B: Berkshire Hathaway, 伯克希尔, Warren Buffett, 巴菲特
SPY: S&P 500 ETF, 标普500 ETF
QQQ: Nasdaq 100 ETF, 纳指100 ETF
VOO: Vanguard S&P 500 ETF
VTI: Vanguard Total Stock Market ETF
IWM: Russell 2000 ETF
TLT: long Treasury ETF, 长债 ETF
GLD: gold ETF, 黄金 ETF
```

The seed should be stored as data, not hardcoded logic.

## Implementation Phases

### Phase SM-1: Schema And Sync MVP

- Add Alembic migration for `securities`, `security_aliases`, `security_master_sync_runs`, and `security_resolution_failures`.
- Add SQLAlchemy models and store methods.
- Add sync command for Nasdaq Trader and SEC files.
- Add tests with local fixtures.

Completion:

- Local database can be populated from fixture files.
- `MMM` and `ORCL` are present.
- Sync is idempotent.

### Phase SM-2: Resolver Replacement

- Add `SecurityMasterResolver`.
- Replace `LocalTickerDirectory` usage in `WorkflowRouter` with the resolver.
- Keep a small in-memory fixture resolver for tests.
- Preserve the current Copilot API response shape.

Completion:

- "Compare 3M and ORCL from June 2015 to now" resolves to `MMM` and `ORCL`.
- Existing tests for NVDA, AMD, AAPL, healthcare candidates, and person clues still pass through database-backed aliases.

### Phase SM-3: Alias Maintenance

- Do not build admin endpoints or UI for alias review and creation in this phase.
- Maintain aliases directly in the `security_aliases` table during the single-operator demo.
- Store common Chinese names and person clues in `security_aliases`.

Completion:

- Operator can add `甲骨文 -> ORCL` directly in the database without code changes.
- Operator can add `黄仁勋 -> NVDA` directly in the database without code changes.

### Phase SM-4: Production Sync And Monitoring

- Run first production sync manually.
- Add status row showing latest sync time and counts.
- Add safe retry and failure logging.
- Schedule automatic production sync every Monday at 00:00 server time.

Completion:

- Production Copilot resolves common US stock and ETF requests from Security Master.
- Failed query logs provide a practical alias backlog.

## Risks And Controls

Risk: Source files change format.

- Control: parser tests with fixture snapshots and sync-run failure logs.

Risk: Bad alias maps to wrong ticker.

- Control: admin alias source/confidence fields; user confirmation remains mandatory.

Risk: Delisted/obsolete symbols appear.

- Control: status field and active/inactive filtering. Do not silently delete historical entries.

Risk: ETF and share-class ambiguity.

- Control: return candidate lists when confidence is not high.

Risk: Data provider licensing.

- Control: first version uses public Nasdaq Trader and SEC files; optional paid/enriched sources are isolated.

## Stop Criteria For First Implementation

The first code implementation should stop when:

- PostgreSQL stores a Security Master loaded from Nasdaq Trader + SEC source files or local fixtures.
- `MMM`, `ORCL`, common large-cap stocks, and common ETFs can be resolved.
- Chinese/person aliases are represented in `security_aliases`.
- Copilot uses the Security Master resolver instead of the hardcoded tiny directory.
- Tests prove the example "Compare 3M and ORCL from June 2015 to now" routes correctly.
- Docs and Chinese mirror are updated.
