from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from .ticker_directory import LocalTickerDirectory, TickerMatch


@dataclass(frozen=True)
class WorkflowDraft:
    intent: str
    symbols: list[TickerMatch]
    start_date: str | None
    end_date: str | None
    analysis_anchor: str | None
    requires_confirmation: bool
    message: str


class WorkflowRouter:
    """Deterministic Workflow Router for the first Copilot MVP."""

    def __init__(self, directory: LocalTickerDirectory | None = None) -> None:
        self.directory = directory or LocalTickerDirectory()

    def route(self, message: str, today: date | None = None) -> WorkflowDraft:
        today = today or date.today()
        cleaned = message.strip()
        symbols = self._resolve_symbols(cleaned)
        start_date, end_date = self._parse_dates(cleaned, today)
        intent = self._infer_intent(cleaned, symbols)
        requires_confirmation = intent in {"add_to_watchlist", "single_analysis", "multi_compare"}

        return WorkflowDraft(
            intent=intent,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            analysis_anchor=end_date,
            requires_confirmation=requires_confirmation,
            message=self._draft_message(intent, symbols),
        )

    def _resolve_symbols(self, message: str) -> list[TickerMatch]:
        found: dict[str, TickerMatch] = {}
        for chunk in self._candidate_chunks(message):
            matches = self.directory.search(chunk, limit=1)
            if matches:
                found.setdefault(matches[0].ticker, matches[0])
        return list(found.values())

    @staticmethod
    def _candidate_chunks(message: str) -> list[str]:
        separators = r"[\s,，。；;、和与跟及]+"
        chunks = [chunk.strip() for chunk in re.split(separators, message) if chunk.strip()]
        chunks.append(message)
        return chunks

    @staticmethod
    def _parse_dates(message: str, today: date) -> tuple[str | None, str | None]:
        iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", message)
        if iso_dates:
            return None, iso_dates[-1]

        start_date = None
        year_start_match = re.search(r"(\d{4})\s*年初", message)
        if year_start_match:
            start_date = f"{year_start_match.group(1)}-01-01"

        end_date = None
        if any(token in message.casefold() for token in ("现在", "today", "now", "latest")):
            end_date = today.isoformat()

        return start_date, end_date

    @staticmethod
    def _infer_intent(message: str, symbols: list[TickerMatch]) -> str:
        lowered = message.casefold()
        if any(token in message for token in ("股票池", "关注", "加入")) or "watchlist" in lowered:
            return "add_to_watchlist" if symbols else "clarify"
        if any(token in message for token in ("比较", "对比")) or "compare" in lowered:
            return "multi_compare" if len(symbols) >= 2 else "clarify"
        if any(token in message for token in ("研究", "分析", "看看")) or "analyze" in lowered:
            return "single_analysis" if len(symbols) == 1 else "clarify"
        if symbols:
            return "single_analysis" if len(symbols) == 1 else "multi_compare"
        return "clarify"

    @staticmethod
    def _draft_message(intent: str, symbols: list[TickerMatch]) -> str:
        if intent == "clarify":
            return "Please provide a ticker, company name, or person clue so AlphaPilot can identify the stock."
        tickers = ", ".join(symbol.ticker for symbol in symbols)
        if intent == "multi_compare":
            return f"Confirm these tickers for comparison: {tickers}."
        if intent == "add_to_watchlist":
            return f"Confirm adding these tickers to your watchlist: {tickers}."
        return f"Confirm starting analysis for: {tickers}."
