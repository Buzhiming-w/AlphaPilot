from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from .settings import get_copilot_llm_model, get_copilot_llm_provider, is_copilot_llm_enabled
from .ticker_directory import LocalTickerDirectory, TickerMatch


@dataclass(frozen=True)
class WorkflowDraft:
    intent: str
    symbols: list[TickerMatch]
    candidate_groups: list["TickerCandidateGroup"]
    unresolved_entities: list[str]
    start_date: str | None
    end_date: str | None
    analysis_anchor: str | None
    requires_confirmation: bool
    message: str


@dataclass(frozen=True)
class TickerCandidateGroup:
    query: str
    candidates: list[TickerMatch]


class WorkflowRouter:
    """Deterministic Workflow Router for the first Copilot MVP."""

    def __init__(self, directory: LocalTickerDirectory | None = None) -> None:
        self.directory = directory or LocalTickerDirectory()

    def route(self, message: str, today: date | None = None) -> WorkflowDraft:
        today = today or date.today()
        cleaned = message.strip()
        llm_hint = self._interpret_with_llm(cleaned) if is_copilot_llm_enabled() else {}
        symbols, candidate_groups, unresolved_entities = self._resolve_draft_entities(
            cleaned,
            llm_symbols=llm_hint.get("symbols", []),
        )
        discovered = False
        if not symbols:
            symbols = self._discover_symbols(cleaned)
            discovered = bool(symbols)
            if discovered:
                candidate_groups = [
                    TickerCandidateGroup(query="discovered candidates", candidates=symbols),
                ]
                unresolved_entities = []
        start_date, end_date = self._parse_dates(cleaned, today)
        start_date = llm_hint.get("start_date") or start_date
        end_date = llm_hint.get("end_date") or end_date
        intent = self._normalize_intent(llm_hint.get("intent")) or self._infer_intent(cleaned, symbols)
        if candidate_groups and not symbols:
            intent = "analysis" if intent == "clarify" else intent
        requires_confirmation = intent in {"analysis", "compare"} and bool(symbols) and not unresolved_entities

        return WorkflowDraft(
            intent=intent,
            symbols=symbols,
            candidate_groups=candidate_groups,
            unresolved_entities=unresolved_entities,
            start_date=start_date,
            end_date=end_date,
            analysis_anchor=end_date,
            requires_confirmation=requires_confirmation,
            message=self._draft_message(
                intent,
                symbols,
                candidate_groups=candidate_groups,
                unresolved_entities=unresolved_entities,
                discovered=discovered,
            ),
        )

    @staticmethod
    def _normalize_intent(intent: str | None) -> str | None:
        if not intent:
            return None
        lowered = intent.casefold().strip()
        if lowered in {"compare", "multi_compare", "comparison"}:
            return "compare"
        if lowered in {"analysis", "single_analysis", "multi_analysis", "add_to_watchlist", "watchlist"}:
            return "analysis"
        if lowered in {"clarify", "unsupported"}:
            return lowered
        return None

    @staticmethod
    def _interpret_with_llm(message: str) -> dict:
        prompt = (
            "You are AlphaPilot's server-side workflow router. "
            "Extract the user's investment research request as strict JSON only. "
            "Schema: {\"intent\":\"analysis|compare|clarify|unsupported\","
            "\"symbols\":[\"ticker, company, alias, or person clue\"],"
            "\"start_date\":\"YYYY-MM-DD or null\",\"end_date\":\"YYYY-MM-DD or null\"}. "
            "Use compare only for explicit cross-stock comparison. "
            f"User request: {message}"
        )
        try:
            from tradingagents.llm_clients.factory import create_llm_client

            client = create_llm_client(
                provider=get_copilot_llm_provider(),
                model=get_copilot_llm_model(),
                temperature=0,
            ).get_chat_model()
            response = client.invoke(prompt)
            content = getattr(response, "content", response)
            if isinstance(content, list):
                content = " ".join(str(part) for part in content)
            text = str(content).strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL)
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _resolve_symbols(self, message: str) -> list[TickerMatch]:
        found: dict[str, TickerMatch] = {}
        for chunk in self._candidate_chunks(message):
            for match in self.directory.search(chunk, limit=5):
                found.setdefault(match.ticker, match)
        return list(found.values())

    def _resolve_draft_entities(
        self,
        message: str,
        *,
        llm_symbols: list[str],
    ) -> tuple[list[TickerMatch], list[TickerCandidateGroup], list[str]]:
        queries = llm_symbols or self._entity_queries(message)
        selected: dict[str, TickerMatch] = {}
        candidate_groups: list[TickerCandidateGroup] = []
        unresolved: list[str] = []

        for query in queries:
            matches = self.directory.search(query, limit=5)
            if not matches:
                unresolved.append(query)
                continue
            candidate_groups.append(TickerCandidateGroup(query=query, candidates=matches))
            if self._is_confident_single_candidate(matches):
                selected.setdefault(matches[0].ticker, matches[0])

        return list(selected.values()), candidate_groups, unresolved

    @staticmethod
    def _is_confident_single_candidate(matches: list[TickerMatch]) -> bool:
        if not matches:
            return False
        top = matches[0]
        if len(matches) == 1:
            return top.confidence == "high"
        return top.confidence == "high" and top.match_reason != "Partial text match"

    def _discover_symbols(self, message: str) -> list[TickerMatch]:
        lowered = message.casefold()
        wants_healthcare = any(token in message for token in ("医疗", "医药", " healthcare", "健康")) or any(
            token in lowered for token in ("healthcare", "health care", "medical", "pharma")
        )
        wants_large_cap = any(token in message for token in ("市值最大", "最大市值", "龙头", "最大的")) or any(
            token in lowered for token in ("largest", "mega cap", "large cap", "biggest")
        )
        if wants_healthcare and wants_large_cap:
            candidates: list[TickerMatch] = []
            for ticker in ("LLY", "UNH", "JNJ"):
                match = self.directory.search(ticker, limit=1)
                if match:
                    candidates.append(match[0])
            return candidates
        return []

    @staticmethod
    def _candidate_chunks(message: str) -> list[str]:
        separators = r"[\s,，。；;、和与跟及]+"
        chunks: list[str] = []
        for chunk in re.split(separators, message):
            chunk = chunk.strip()
            if not chunk:
                continue
            chunks.append(chunk)
            chunks.extend(re.findall(r"[A-Za-z0-9][A-Za-z0-9.]*", chunk))
        chunks.append(message)
        return chunks

    @classmethod
    def _entity_queries(cls, message: str) -> list[str]:
        split_pattern = r",|，|;|；|、|\s+(?:and|vs|versus)\s+|和|与|跟|及|对比|比较"
        queries: list[str] = []
        for raw_part in re.split(split_pattern, message, flags=re.IGNORECASE):
            query = cls._clean_entity_query(raw_part)
            if query:
                queries.append(query)
        if not queries:
            fallback = cls._clean_entity_query(message)
            if fallback:
                queries.append(fallback)
        return queries

    @staticmethod
    def _clean_entity_query(value: str) -> str:
        query = value.strip()
        query = re.sub(r"^\s*(帮我|请|把|please|help me|analyze|分析|研究|看看|compare)\s*", "", query, flags=re.IGNORECASE)
        query = re.sub(r"^\s*(from|从)\s+.*$", "", query, flags=re.IGNORECASE)
        query = re.sub(r"\s*(从|自)\s*\d{4}.*$", "", query)
        query = re.sub(r"\s*(\d{4}-\d{2}-\d{2}|\d{4}\s*年.*)$", "", query)
        query = re.sub(r"\s*(加入股票池|加入关注|两只股票|这些股票|这几只股票|股票|表现|的表现|走势|进行分析|分析)$", "", query)
        query = re.sub(r"\s*(的公司|公司)$", "", query)
        query = query.strip(" .。")
        if not query:
            return ""
        ticker_tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9.]{0,9}", query)
        if ticker_tokens and re.fullmatch(r"[A-Za-z0-9.]+[\u4e00-\u9fff].*", query):
            return ticker_tokens[0]
        if ticker_tokens and not re.search(r"[\u4e00-\u9fff]", query):
            return " ".join(ticker_tokens)
        return query

    @staticmethod
    def _parse_dates(message: str, today: date) -> tuple[str | None, str | None]:
        iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", message)
        if iso_dates:
            return None, iso_dates[-1]

        start_date = None
        month_name_match = re.search(
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
            message,
            flags=re.IGNORECASE,
        )
        if month_name_match:
            month_names = {
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "may": 5,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12,
            }
            month = month_names[month_name_match.group(1).casefold()]
            start_date = f"{month_name_match.group(2)}-{month:02d}-01"

        chinese_month_match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", message)
        if chinese_month_match:
            start_date = f"{chinese_month_match.group(1)}-{int(chinese_month_match.group(2)):02d}-01"

        year_start_match = re.search(r"(\d{4})\s*年初", message)
        if year_start_match:
            start_date = f"{year_start_match.group(1)}-01-01"

        end_date = None
        if any(token in message.casefold() for token in ("现在", "至今", "today", "now", "latest")):
            end_date = today.isoformat()

        return start_date, end_date

    @staticmethod
    def _infer_intent(message: str, symbols: list[TickerMatch]) -> str:
        lowered = message.casefold()
        if any(token in message for token in ("比较", "对比")) or "compare" in lowered:
            return "compare" if len(symbols) >= 2 else "clarify"
        if any(token in message for token in ("研究", "分析", "看看", "股票池", "关注", "加入")) or "analyze" in lowered or "watchlist" in lowered:
            return "analysis" if symbols else "clarify"
        if symbols:
            return "analysis"
        return "clarify"

    @staticmethod
    def _draft_message(
        intent: str,
        symbols: list[TickerMatch],
        *,
        candidate_groups: list[TickerCandidateGroup],
        unresolved_entities: list[str],
        discovered: bool = False,
    ) -> str:
        if unresolved_entities:
            return (
                "Some entities need more information before AlphaPilot can start the workflow. "
                "Please provide a ticker, company name, or person clue."
            )
        if candidate_groups and not symbols:
            return "Select the intended ticker from the candidate list before confirming."
        if intent == "clarify":
            return "Please provide a ticker, company name, or person clue so AlphaPilot can identify the stock."
        tickers = ", ".join(symbol.ticker for symbol in symbols)
        if intent == "compare":
            return f"Confirm these tickers for comparison: {tickers}."
        if discovered:
            return f"Confirm these candidates for analysis: {tickers}."
        return f"Confirm starting analysis for: {tickers}."
