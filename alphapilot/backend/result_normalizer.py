from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEMO_SUMMARY_PATH = Path(".alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json")
DEMO_STATE_PATH = Path(
    ".alphapilot_runtime/results/NVDA/TradingAgentsStrategy_logs/full_states_log_2024-05-10.json"
)


SECTION_FIELDS = {
    "market": "market_report",
    "sentiment": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
    "investment": "investment_plan",
    "trader": "trader_investment_decision",
    "final": "final_trade_decision",
}


def normalize_engine_state(
    state: dict[str, Any],
    *,
    processed_decision: str | None = None,
) -> dict[str, Any]:
    """Convert raw TradingAgents state/log JSON into frontend API shape."""
    trader_text = state.get("trader_investment_decision") or state.get(
        "trader_investment_plan", ""
    )
    merged_state = {**state, "trader_investment_decision": trader_text}
    sections = {
        name: str(merged_state.get(field, "") or "").strip()
        for name, field in SECTION_FIELDS.items()
        if str(merged_state.get(field, "") or "").strip()
    }

    return {
        "ticker": state.get("company_of_interest") or state.get("ticker"),
        "trade_date": state.get("trade_date"),
        "decision": processed_decision or state.get("decision") or "Unknown",
        "sections": sections,
        "debates": {
            "investment": state.get("investment_debate_state", {}),
            "risk": state.get("risk_debate_state", {}),
        },
    }


def load_demo_result() -> tuple[dict[str, Any], dict[str, Any]]:
    summary = json.loads(DEMO_SUMMARY_PATH.read_text(encoding="utf-8"))
    raw_state = json.loads(DEMO_STATE_PATH.read_text(encoding="utf-8"))
    normalized = normalize_engine_state(
        raw_state,
        processed_decision=summary.get("decision"),
    )
    normalized["elapsed_seconds"] = summary.get("elapsed_seconds")
    normalized["llm_provider"] = summary.get("llm_provider")
    normalized["selected_analysts"] = summary.get("selected_analysts", ["market"])
    return normalized, raw_state
