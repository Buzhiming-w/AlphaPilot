import pytest

from tradingagents.graph.trading_graph import TradingAgentsGraph


@pytest.mark.unit
def test_market_tool_node_includes_verified_snapshot():
    graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
    market_tools = graph._create_tool_nodes()["market"].tools_by_name

    assert "get_stock_data" in market_tools
    assert "get_indicators" in market_tools
    assert "get_verified_market_snapshot" in market_tools


@pytest.mark.unit
def test_fetch_returns_is_unavailable_when_yfinance_missing(monkeypatch):
    import tradingagents.graph.trading_graph as trading_graph

    monkeypatch.setattr(trading_graph, "yf", None)
    graph = TradingAgentsGraph.__new__(TradingAgentsGraph)

    assert graph._fetch_returns("NVDA", "2024-05-10") == (None, None, None)
