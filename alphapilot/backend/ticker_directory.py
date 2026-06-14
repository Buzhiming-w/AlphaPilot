from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class TickerMatch:
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    confidence: str
    match_reason: str


@dataclass(frozen=True)
class TickerRecord:
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    aliases: tuple[str, ...]
    people: tuple[str, ...] = ()


US_EQUITY_RECORDS: tuple[TickerRecord, ...] = (
    TickerRecord(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("nvidia", "nvidia corporation", "英伟达", "辉达"),
        people=("jensen huang", "huang renxun", "黄仁勋"),
    ),
    TickerRecord(
        ticker="AMD",
        company_name="Advanced Micro Devices, Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("amd", "advanced micro devices", "超威半导体"),
        people=("lisa su", "su zifeng", "苏姿丰"),
    ),
    TickerRecord(
        ticker="AAPL",
        company_name="Apple Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("apple", "apple inc", "苹果", "苹果公司"),
        people=("tim cook", "蒂姆库克", "库克"),
    ),
    TickerRecord(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("microsoft", "microsoft corporation", "微软"),
        people=("satya nadella", "纳德拉"),
    ),
    TickerRecord(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("alphabet", "google", "谷歌", "字母表"),
        people=("sundar pichai", "皮查伊"),
    ),
    TickerRecord(
        ticker="AMZN",
        company_name="Amazon.com, Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("amazon", "amazon.com", "亚马逊"),
        people=("andy jassy", "jeff bezos", "贝索斯"),
    ),
    TickerRecord(
        ticker="META",
        company_name="Meta Platforms, Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("meta", "facebook", "meta platforms", "脸书"),
        people=("mark zuckerberg", "扎克伯格"),
    ),
    TickerRecord(
        ticker="TSLA",
        company_name="Tesla, Inc.",
        market="US",
        exchange="NASDAQ",
        currency="USD",
        aliases=("tesla", "特斯拉"),
        people=("elon musk", "马斯克"),
    ),
    TickerRecord(
        ticker="BRK.B",
        company_name="Berkshire Hathaway Inc.",
        market="US",
        exchange="NYSE",
        currency="USD",
        aliases=("berkshire", "berkshire hathaway", "伯克希尔"),
        people=("warren buffett", "巴菲特"),
    ),
)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("，", " ").replace(",", " ").split())


class LocalTickerDirectory:
    """Small deterministic US-equity lookup for the Workflow Router MVP."""

    def __init__(self, records: tuple[TickerRecord, ...] = US_EQUITY_RECORDS) -> None:
        self.records = records

    def search(self, query: str, limit: int = 5) -> list[TickerMatch]:
        normalized_query = _normalize(query)
        if not normalized_query:
            return []

        scored: list[tuple[int, TickerRecord, str, str]] = []
        for record in self.records:
            score, reason, confidence = self._score_record(record, normalized_query)
            if score > 0:
                scored.append((score, record, reason, confidence))

        scored.sort(key=lambda item: (-item[0], item[1].ticker))
        return [
            TickerMatch(
                ticker=record.ticker,
                company_name=record.company_name,
                market=record.market,
                exchange=record.exchange,
                currency=record.currency,
                confidence=confidence,
                match_reason=reason,
            )
            for _, record, reason, confidence in scored[:limit]
        ]

    def _score_record(self, record: TickerRecord, normalized_query: str) -> tuple[int, str, str]:
        ticker = _normalize(record.ticker)
        company_name = _normalize(record.company_name)
        aliases = tuple(_normalize(alias) for alias in record.aliases)
        people = tuple(_normalize(person) for person in record.people)

        if normalized_query == ticker:
            return 100, "Exact ticker match", "high"
        if normalized_query == company_name:
            return 95, "Exact company name match", "high"
        if normalized_query in aliases:
            return 90, "Alias match", "high"
        if normalized_query in people:
            return 88, "Person clue match", "high"

        searchable_terms = (ticker, company_name, *aliases, *people)
        if any(normalized_query in term or term in normalized_query for term in searchable_terms):
            return 70, "Partial text match", "medium"

        best_ratio = max(SequenceMatcher(None, normalized_query, term).ratio() for term in searchable_terms)
        if len(normalized_query) >= 4 and best_ratio >= 0.82:
            return int(best_ratio * 60), "Fuzzy text match", "medium"

        return 0, "", "low"
