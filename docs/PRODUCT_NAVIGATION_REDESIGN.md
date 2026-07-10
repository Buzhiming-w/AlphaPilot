# Product Navigation Redesign

Last updated: 2026-06-15

## Goal

Simplify AlphaPilot's product navigation around the actual analysis workflow instead of exposing MVP-era implementation pages.

The product should feel like a research workspace with two core analysis modes:

- `Analysis`: single-stock or multi-stock research analysis.
- `Compare`: explicit cross-stock comparison.

`Dashboard` remains the starting point for Copilot, status, and recent activity.

## Primary Navigation

Left sidebar should contain only:

```text
Dashboard
Analysis
Compare
```

The sidebar should not contain:

- `Login`
- `New Analysis`
- `Report Detail`
- `Watchlist`
- `Admin Users`
- `Public Demo`

## Top-Right Account Area

Authentication and admin controls should move out of the left sidebar.

Top-right behavior:

- Logged-out users see `Login`.
- Logged-in users see the current user's display name in the top-right account area.
- If `display_name` is unavailable, the UI may fall back to the user's email.
- The same account area should show compact quota/account state and account actions.
- Logged-in users should have an explicit `Logout` action.
- The logged-in user's display name should be shown as a non-primary account label or badge, not as the main yellow action button.
- Admin controls are visible only to admin users.
- The admin-only user management entry should be labeled `Manage Users`, not `Admin`, because the current admin surface is specifically for managing user accounts.
- Clicking `Manage Users` should open a user management interface where admins can view users, enable/disable accounts, and adjust regular-user quota settings.
- Regular users should not see the `Manage Users` action.
- Regular users should have a daily quota of 3 live workflows.
- Admin users should not be limited by daily quota, but they should still be protected by system-level rate limiting and worker capacity limits.
- The quota UI should not show `used / 3` for admin users. It should show an admin-specific state such as `Admin access` or `Unlimited`, while making clear that system-level safety limits still apply.

`Admin Users` should not be a normal primary navigation item.

## Branding Copy

Product-facing copy should use AlphaPilot's own positioning rather than referencing an inspiration source.

- The top page eyebrow currently showing `OpenBB-inspired analyst workspace` should be changed to `Agentic stock research terminal`.
- The left brand block should show `AlphaPilot` without the small secondary `Research terminal` text beside it.
- OpenBB can remain in internal docs as a design inspiration for dense financial-workspace styling, but the product UI should not display `OpenBB-inspired` because AlphaPilot does not depend on or integrate the OpenBB library.

## Dashboard Behavior

Dashboard is the research command center.

It should contain:

- A simplified natural-language Copilot conversation.
- Recent activity or recent analysis summary.
- Product status and quota/account state.
- Public demo content for unauthenticated visitors when appropriate.
- A compact `How to use AlphaPilot` guide so first-time users understand the product workflow.

The current single-line disclaimer should be replaced by a useful Dashboard guide panel. The non-advice warning should remain, but it should be part of the guide instead of the only explanation users see.

Recommended regular-user guide copy:

```text
How to use AlphaPilot

1. Describe your research goal in Copilot
Ask in natural language, for example: "Compare Tesla and AMD from the start of 2024 to now" or "Find large-cap US healthcare stocks and analyze YTD performance."

2. Confirm the interpreted workflow
AlphaPilot resolves tickers, dates, and whether the request belongs in Analysis or Compare. Confirm only when the draft is correct.

3. Follow progress in Analysis or Compare
After confirmation, the workflow starts automatically. Open Analysis for single or multi-stock research, or Compare for explicit cross-stock comparisons.

4. Read the final report
Reports are research assistance only. They are not financial advice and AlphaPilot does not execute trades.
```

Recommended admin-only guide addition:

```text
Admin tools
Use Manage Users to review registered users, enable or disable accounts, and adjust regular-user quota settings. Admin accounts are not limited by daily workflow quota, but system-level rate limits and worker capacity still apply.
```

Guide display rules:

- Logged-out users may see the regular guide plus a login prompt.
- Regular logged-in users see the regular guide only.
- Admin users see the regular guide plus the `Admin tools` addition.
- The guide should be concise enough to stay useful on the Dashboard and should not become a long documentation page.

It should not contain the legacy top-right quick analysis form:

```text
ticker
trade_date
Run analysis
```

It should not show a stale demo rating as the current decision.

Current issue to fix:

- The Dashboard metric card currently shows `Decision: Overweight` from the saved NVDA Phase 1 demo.
- That value can be mistaken for the result of the user's current Copilot request.
- If no active analysis is selected, Dashboard should show `No active analysis`, `No current decision`, or a clearly labeled `Latest demo result`.
- If the saved demo remains visible, it must be labeled as `Demo result`, not as the current workspace decision.
- `Overweight`, `Neutral`, and `Underweight` ratings should appear in `Analysis` or `Compare` result states, or in explicitly labeled demo summaries.
- The Dashboard `Runtime` metric currently remains `--` after a workflow has completed.
- Runtime should be populated from the selected or most recent completed analysis job when that job has elapsed/runtime metadata.
- If no active, selected, or recently completed job has runtime metadata, the metric may stay `--`; otherwise it should show a human-readable duration such as `267s` or `4m 27s`.
- This should be investigated together with the broader Dashboard metric binding pass after the current product feedback list is confirmed.

After Copilot understands the user's request:

- `single_analysis` or general analysis requests should route to `Analysis`.
- multi-stock analysis requests that are not explicit comparisons should route to `Analysis`.
- explicit comparison requests should route to `Compare`.
- the target page should load the confirmed symbols, date range, and analysis interface.

## Copilot Conversation Model

The Copilot UI should be simplified from a button-heavy router into a natural-language confirmation flow.

The Copilot should not show workflow shortcut buttons such as:

- `Watchlist`
- `Single`
- `Route workflow`
- intent-specific action buttons that look like separate product choices.

Preferred flow:

1. The user enters a natural-language request in the conversation box.
2. The user clicks one `Enter` / submit button to send the natural-language request.
3. The backend calls the LLM server-side to interpret the request into a structured analysis draft.
4. The UI shows a clear summary of what will be analyzed:
   - target section: `Analysis` or `Compare`;
   - resolved ticker symbols and company names;
   - date or date range;
   - analysis mode and important assumptions;
   - any ambiguity or missing information.
5. The user clicks one `Confirm` button only when the analysis content is correct.
6. After confirmation, AlphaPilot sends the draft into the configured workflow and navigates to `Analysis` or `Compare`.

Correction flow:

- If the analysis content is wrong, the user should not need to click multiple workflow buttons.
- The user can keep typing natural-language corrections in the same conversation box.
- Each correction updates the existing draft instead of starting from a blank workflow.
- Examples:
  - "不是 Facebook，是 Ford"
  - "时间改成 2024 年初到现在"
  - "加上 AMD 一起分析"
  - "这不是 compare，只做普通多股票分析"
- The UI should keep showing the latest interpreted draft until the user confirms it.

Backend behavior:

- LLM interpretation must happen server-side; provider API keys must never reach the frontend.
- The LLM should return structured output, not free-form instructions.
- Deterministic ticker validation can still be used after LLM parsing to verify symbols and reduce hallucinated tickers.
- When the user's request is fuzzy but contains useful constraints, Copilot should return candidate symbols instead of immediately asking the user to provide a ticker.
- The workflow should not start until the user confirms the draft.

Fuzzy stock discovery:

- Copilot should handle requests such as "largest US healthcare stock year-to-date performance" even when no exact ticker or company name is provided.
- First-version discovery can use a curated deterministic directory for common high-value cases, then fall back to optional server-side LLM parsing.
- The UI should show a candidate list with ticker, company name, exchange, and currency, then ask the user to confirm or correct the draft.
- If candidates are uncertain, the draft should remain a confirmation step and must not auto-start the workflow.
- Future versions can replace or extend the curated directory with an external market/security master provider.

Draft refinement:

- Resolved stocks should be rendered as removable chips, not only as plain text. Each chip should show ticker, company name, and a remove action.
- If Copilot resolves extra stocks, the user should be able to remove the wrong chip before confirming.
- If one user-mentioned entity has multiple candidate matches, the UI should show candidate choices for that entity and require the user to select the intended ticker before final confirmation.
- If the user says a candidate is wrong, the same Copilot input should allow a correction such as "not that one, use Oracle" or "only keep ORCL and MMM", and the draft should update in place.
- If some requested entities are unresolved, the draft should clearly show which entities need more information instead of hiding them inside a generic clarification message.
- `Compare` confirmation must validate that the final selected symbol set contains 2 to 5 stocks.
- `Analysis` confirmation may proceed with 1 or more selected stocks.
- For multi-stock analysis, each selected chip should create its own analysis job after confirmation.
- For compare workflows, the final chip set should create one compare workflow after confirmation.

The expected user experience is:

```text
User natural language -> LLM interprets draft -> User confirms or corrects -> Workflow starts
```

## Analysis Section

`Analysis` replaces the old `New Analysis` and `Report Detail` primary navigation items.

It should support:

- single-stock analysis;
- multi-stock analysis;
- creation of a new analysis from manually entered inputs;
- creation of a new analysis from Copilot-confirmed inputs;
- analysis history;
- deleting any analysis history item, including completed, failed, running, or queued jobs;
- opening a completed or running analysis detail from history.

The detail view is a state inside `Analysis`, not a sidebar item.

Deleting an analysis item should remove the job from history, remove its persisted result/progress events, and let the worker safely skip the job if it later sees a stale queue entry.

Manual analysis entry should be secondary:

- Dashboard Copilot confirmation should create/start the analysis workflow before navigating to `Analysis`.
- The user should not need to click another `Start Workflow` button after confirming a Dashboard draft.
- The manual analysis form should live inside a collapsed `Manual analysis` section by default.
- The manual section is only for creating a separate workflow directly from the `Analysis` page.

## Live Analysis Reporting Experience

When an `Analysis` or `Compare` workflow is running, the report screen should not feel like a black-box wait state.

Expected experience:

- Show the active workflow stage, such as ticker resolution, market data collection, analyst reasoning, bull/bear debate, trader plan, risk review, and final decision.
- Stream stage updates into the report view while the backend workflow is running.
- Use a typewriter-style reveal for narrative text so users can see the report forming progressively.
- Add a persistent live status header at the top of the `Progress` panel so a running workflow never looks frozen.
- The status header should show the current state, elapsed timer, latest update age, and a subtle live indicator while queued or running.
- Add a stage-based progress bar rather than a fake precise percentage bar.
- The progress bar should highlight completed stages, the current running stage, and remaining stages.
- `Analysis` stage labels should map to the research workflow, for example: `Ticker`, `Market data`, `Analyst`, `Debate`, `Risk`, `Final`.
- `Compare` stage labels should map to the comparison workflow, for example: `Ticker`, `Data`, `Per-stock analysis`, `Cross-stock comparison`, `Final summary`.
- If no new progress event arrives for a threshold such as 60 seconds while the job is still queued or running, the UI should show a calm liveness message such as `Still running. Waiting for next worker update.` instead of appearing stuck.
- Display short interim conclusions when a stage completes, for example: what data was collected, what signal was found, what uncertainty remains, and what the next stage will evaluate.
- Clearly label interim content as in-progress and not final investment output.
- Replace or reconcile interim text with the persisted final report when the workflow finishes.
- Final reports should be rendered as formatted Markdown, not shown as raw Markdown text in a `<pre>`-style block.
- The rendered report should support headings, paragraphs, bullet and numbered lists, emphasis, blockquotes, tables, horizontal rules, and code/preformatted blocks.
- Markdown tables are especially important because analyst outputs often contain metrics, ratios, and comparison grids.
- The report renderer must sanitize output before injecting HTML into the page; LLM-generated Markdown should never be trusted as raw HTML.
- The reading view should use report-specific typography and spacing so the output feels like a financial research note rather than terminal text.
- A future optional raw/source toggle may be added for debugging or copying the original Markdown, but the default user-facing view should be rendered.
- Preserve completed reports in history so reopening an old report shows the stable final result, not the transient stream.

Implementation direction:

- The backend should emit structured progress events from the analysis worker, not free-form frontend-only fake progress.
- Events should include a stage key, user-facing stage label, status, optional summary text, and timestamps.
- The frontend should subscribe to progress through a polling endpoint first; Server-Sent Events or WebSocket can be added later if needed.
- The frontend should derive elapsed time and latest update age locally from persisted job/progress timestamps, so the timer can keep moving between polling responses.
- The frontend should not pretend to know exact completion percentage unless the backend later provides reliable progress weights.
- The frontend may apply the typewriter animation locally, but the content should come from real workflow progress or saved stage summaries.
- The frontend should use a safe Markdown rendering path for final reports. If a third-party Markdown parser is introduced, it should be paired with sanitization and kept compatible with the static frontend deployment model.
- If streaming fails, the workflow should still complete normally and the UI should fall back to a clear queued/running/completed status.

## Compare Section

`Compare` is for explicit cross-stock comparison.

It should support:

- comparison creation from manually entered inputs;
- comparison creation from Copilot-confirmed inputs;
- compare workflow history;
- deleting compare history items;
- opening a completed or running compare detail from history.

`Compare` should remain separate from `Analysis` because its user intent is different: the user is asking which asset, company, or group looks better under a shared frame.

Manual compare entry should also be secondary:

- Dashboard Copilot confirmation should create the compare workflow before navigating to `Compare`.
- The manual compare form should live inside a collapsed `Manual compare` section by default.
- The manual section is only for creating a separate compare setup directly from the `Compare` page.

## Language and Report Localization

AlphaPilot should support two separate language controls:

1. Global UI language.
2. Report language.

Global UI language:

- Add an `EN` / `中文` toggle in the top-right account area, placed to the left of the user/account button.
- The global UI language controls interface copy only: navigation, buttons, forms, empty states, status labels, Copilot instructions, history labels, progress labels, login/account/admin copy, and disclaimers.
- English UI should remain close to the current interaction model.
- Chinese UI should translate and rewrite all user-facing interaction and display copy into natural Chinese, not machine-like literal translations.
- Persist the user's UI language preference locally first, for example in `localStorage`; account-level persistence can be added later.

Report language:

- `Analysis` and `Compare` report panels should each include an independent report language toggle, such as `Report: English | 中文`.
- The report language toggle is separate from the global UI language toggle.
- In both English and Chinese UI modes, the default report view should show the original English report first because US equity research, filings, metrics, and market terminology are most accurate in English.
- After the English final report completes, AlphaPilot should automatically generate a Chinese report version in the background.
- The Chinese report should be generated from the completed English report as a faithful translation/adaptation, not by rerunning the stock analysis from scratch.
- The translated Chinese report should preserve the same investment conclusion, structure, key numbers, tables, ticker symbols, citations/source names if present, and important English financial terms where useful.
- Chinese report generation should be persisted or cached so switching languages does not repeatedly consume LLM quota.
- While the Chinese report is still being generated, the report toggle may be disabled for Chinese or show a status such as `Chinese report generating`.
- If Chinese report generation fails, the UI should keep the English report visible and show a clear retry/fallback state.

Implementation note:

- Local backend implementation now keeps `TRADINGAGENTS_OUTPUT_LANGUAGE=English` for canonical source reports, generates and caches a full Chinese report under `localized_sections.zh.report` from the completed English report in the background worker when `ALPHAPILOT_REPORT_TRANSLATION_ENABLED=true`, records status in `report_translations.zh`, retries failures according to `ALPHAPILOT_REPORT_TRANSLATION_MAX_ATTEMPTS`, and skips regeneration when a cached Chinese full report already exists. The frontend uses `localized_sections.zh.final` only as a backwards-compatible fallback for older results.

Recommended language strategy:

- `analysis_language`: English.
- `source_report_language`: English.
- `translated_report_language`: Chinese, generated after the English report is complete.
- `ui_language`: controlled by the global UI toggle.
- `report_display_language`: controlled by the report-level toggle and defaults to English.

## Watchlist Decision

`Watchlist` should not be a primary navigation item.

For now, keep backend/storage capability available but hide the frontend primary entry. The current product does not need a standalone stock-saving workflow to support the user's main analysis path.

Future options:

- keep it hidden;
- reintroduce it as `Saved` or `Saved Tickers` inside Dashboard;
- use it only as a source list for Analysis or Compare.

## Implementation Notes

- Frontend navigation should be updated before adding new analysis features.
- Existing backend Watchlist tables and API can remain for now.
- Tests should verify the sidebar contains only `Dashboard`, `Analysis`, and `Compare`.
- Tests should verify `Login`, `Admin`, and account controls are not implemented as ordinary sidebar views.
- Tests should verify a logged-in user's display name is shown in the top-right account area.
- Tests should verify logged-in users have an explicit `Logout` action.
- Tests should verify the display name is shown as an account label or badge rather than the primary yellow action button.
- Tests should verify admin users see `Manage Users`, regular users do not, and clicking `Manage Users` opens the user management interface.
- Tests should verify regular users are limited to 3 live workflows per day.
- Tests should verify admin users bypass daily quota but remain subject to system-level rate limiting and worker capacity controls.
- Tests should verify the quota UI shows an admin-specific state instead of `used / 3` for admin users.
- Tests should verify Dashboard does not present the saved demo `Overweight` rating as the current user workflow decision.
- Tests should verify Dashboard shows a practical `How to use AlphaPilot` guide instead of only a standalone disclaimer.
- Tests should verify regular users do not see admin usage instructions in the Dashboard guide.
- Tests should verify admin users see the `Admin tools` guide addition that explains `Manage Users`, enable/disable accounts, and quota management.
- Tests should verify Dashboard Copilot confirmation routes to the correct section.
- Tests should verify Copilot exposes only a natural-language submit action and a final confirmation action.
- Tests should verify natural-language corrections update the existing draft before workflow confirmation.
- Tests should verify fuzzy requests can resolve candidate stock lists for user confirmation.
- Tests should verify resolved stocks render as removable chips in the Copilot draft.
- Tests should verify users can remove an incorrectly resolved chip before confirming.
- Tests should verify ambiguous entity candidates require a user choice before workflow confirmation.
- Tests should verify unresolved entities are shown separately and do not silently disappear from the draft.
- Tests should verify `Compare` confirmation requires 2 to 5 final selected stocks.
- Tests should verify `Analysis` confirmation allows 1 or more final selected stocks.
- Tests should verify analysis and compare history items can be deleted.
- Tests should verify deleted queued jobs are skipped safely by the worker.
- Tests should verify running reports show real workflow progress instead of only a blank wait state.
- Tests should verify running `Analysis` and `Compare` progress panels include a live status header with elapsed time, latest update age, and a stage-based progress bar.
- Tests should verify the progress bar uses workflow stages instead of a misleading precise percentage when no backend percentage exists.
- Tests should verify final persisted reports replace or reconcile in-progress streamed text after completion.
- Tests should verify final reports render Markdown into structured HTML for headings, lists, and tables instead of displaying raw Markdown markers as the primary view.
- Tests should verify Markdown rendering sanitizes unsafe HTML/script content.
- Tests should verify the global `EN` / `中文` UI toggle changes navigation, controls, status labels, and empty states without changing the selected report language.
- Tests should verify `Analysis` and `Compare` reports default to English in both UI languages.
- Tests should verify a Chinese report version is generated after the English report completes and can be selected from the report-level language toggle without rerunning the analysis.
- Tests should verify translated Chinese reports are cached or persisted and do not regenerate on every toggle.
- Tests should verify manual Analysis and Compare forms are collapsed by default so Dashboard-confirmed workflows are not confused with a second start action.
