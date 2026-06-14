from __future__ import annotations

from typing import Any

from .result_normalizer import load_demo_result, normalize_engine_state


class AnalysisEngineService:
    """Boundary between product API code and the TradingAgents engine."""

    def run_demo(self) -> tuple[dict[str, Any], dict[str, Any]]:
        return load_demo_result()

    def run_live(
        self,
        ticker: str,
        trade_date: str,
        selected_analysts: list[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        config = DEFAULT_CONFIG.copy()
        graph = TradingAgentsGraph(
            selected_analysts=selected_analysts or ["market"],
            config=config,
        )
        final_state, decision = graph.propagate(ticker, trade_date)
        normalized = normalize_engine_state(final_state, processed_decision=decision)
        return normalized, final_state
