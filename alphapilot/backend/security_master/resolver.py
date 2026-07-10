from __future__ import annotations

from alphapilot.backend.ticker_directory import TickerMatch


class SecurityMasterResolver:
    """Ticker resolver backed by AlphaPilot's Security Master store methods."""

    def __init__(self, store) -> None:
        self.store = store

    def search(self, query: str, limit: int = 5) -> list[TickerMatch]:
        matches = self.store.search_security_master(query, limit=limit)
        return [
            TickerMatch(
                ticker=security.symbol,
                company_name=security.name,
                market=security.market,
                exchange=security.exchange,
                currency=security.currency,
                confidence=confidence,
                match_reason=reason,
            )
            for security, reason, confidence in matches
        ]
