"""Run a small AlphaPilot engine smoke test.

This keeps Phase 1 verification cheaper than the full CLI/main.py run while
still exercising the TradingAgents graph through to a final decision.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


TICKER = "NVDA"
TRADE_DATE = "2024-05-10"
OUTPUT_DIR = Path(".alphapilot_runtime/demo_outputs")


def main() -> None:
    started_at = time.time()
    config = DEFAULT_CONFIG.copy()
    config["timeout"] = 45
    config["max_retries"] = 0
    config["max_recur_limit"] = 20
    config["memory_log_path"] = str(
        OUTPUT_DIR / f"phase1_smoke_memory_{TICKER}_{TRADE_DATE}_{int(started_at)}.md"
    )

    print("Initializing TradingAgentsGraph...", flush=True)
    graph = TradingAgentsGraph(
        selected_analysts=["market"],
        debug=os.getenv("ALPHAPILOT_SMOKE_DEBUG") == "1",
        config=config,
    )
    print("Starting graph propagation...", flush=True)
    final_state, decision = graph.propagate(TICKER, TRADE_DATE)
    print("Graph propagation completed.", flush=True)

    elapsed_seconds = round(time.time() - started_at, 2)
    result = {
        "ticker": TICKER,
        "trade_date": TRADE_DATE,
        "asset_type": final_state.get("asset_type", "stock"),
        "llm_provider": config.get("llm_provider"),
        "quick_think_llm": config.get("quick_think_llm"),
        "deep_think_llm": config.get("deep_think_llm"),
        "selected_analysts": ["market"],
        "elapsed_seconds": elapsed_seconds,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "final_trade_decision": final_state.get("final_trade_decision"),
        "available_sections": sorted(
            key
            for key in (
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
                "investment_plan",
                "trader_investment_plan",
                "final_trade_decision",
            )
            if final_state.get(key)
        ),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"phase1_smoke_{TICKER}_{TRADE_DATE}.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"AlphaPilot Phase 1 smoke run completed in {elapsed_seconds}s")
    print(f"Output: {output_path}")
    print(f"Decision: {decision}")


if __name__ == "__main__":
    main()
