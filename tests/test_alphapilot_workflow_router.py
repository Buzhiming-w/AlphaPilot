from datetime import date

import pytest

from alphapilot.backend.workflow_router import WorkflowRouter


@pytest.fixture()
def router(monkeypatch):
    monkeypatch.setenv("ALPHAPILOT_COPILOT_LLM_ENABLED", "false")
    return WorkflowRouter()


@pytest.mark.unit
def test_route_multi_compare_with_person_company_and_date_range(router):
    draft = router.route("帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在", today=date(2026, 6, 15))

    assert draft.intent == "compare"
    assert [symbol.ticker for symbol in draft.symbols] == ["NVDA", "AMD"]
    assert draft.start_date == "2024-01-01"
    assert draft.end_date == "2026-06-15"
    assert draft.analysis_anchor == "2026-06-15"
    assert draft.requires_confirmation is True


@pytest.mark.unit
def test_route_compare_with_ticker_touching_chinese_suffix(router):
    draft = router.route("比较3M和orcl两只股票的表现，从2015年6月至今", today=date(2026, 6, 15))

    assert draft.intent == "compare"
    assert [symbol.ticker for symbol in draft.symbols] == ["MMM", "ORCL"]
    assert draft.start_date == "2015-06-01"
    assert draft.end_date == "2026-06-15"


@pytest.mark.unit
def test_route_watchlist_style_request_becomes_analysis_draft(router):
    draft = router.route("把苹果加入股票池", today=date(2026, 6, 15))

    assert draft.intent == "analysis"
    assert [symbol.ticker for symbol in draft.symbols] == ["AAPL"]
    assert draft.requires_confirmation is True


@pytest.mark.unit
def test_route_single_analysis_with_iso_date(router):
    draft = router.route("研究英伟达 2024-05-10", today=date(2026, 6, 15))

    assert draft.intent == "analysis"
    assert [symbol.ticker for symbol in draft.symbols] == ["NVDA"]
    assert draft.start_date is None
    assert draft.end_date == "2024-05-10"
    assert draft.analysis_anchor == "2024-05-10"


@pytest.mark.unit
def test_route_multi_stock_analysis_without_comparison_stays_analysis(router):
    draft = router.route("分析苹果和英伟达，从 2024 年初到现在", today=date(2026, 6, 15))

    assert draft.intent == "analysis"
    assert [symbol.ticker for symbol in draft.symbols] == ["AAPL", "NVDA"]
    assert draft.start_date == "2024-01-01"


@pytest.mark.unit
def test_route_discovers_large_us_healthcare_candidates_from_vague_request(router):
    draft = router.route("美国市值最大的医疗股票 2026年初至今的表现", today=date(2026, 6, 15))

    assert draft.intent == "analysis"
    assert [symbol.ticker for symbol in draft.symbols] == ["LLY", "UNH", "JNJ"]
    assert draft.start_date == "2026-01-01"
    assert draft.end_date == "2026-06-15"
    assert draft.requires_confirmation is True
    assert "candidates" in draft.message.lower()


@pytest.mark.unit
def test_route_exposes_candidate_groups_for_resolved_entities(router):
    draft = router.route("分析苹果和亚马逊", today=date(2026, 6, 15))

    assert [symbol.ticker for symbol in draft.symbols] == ["AAPL", "AMZN"]
    assert [group.query for group in draft.candidate_groups] == ["苹果", "亚马逊"]
    assert [[candidate.ticker for candidate in group.candidates] for group in draft.candidate_groups] == [
        ["AAPL"],
        ["AMZN"],
    ]


@pytest.mark.unit
def test_route_exposes_ambiguous_candidates_without_silently_picking_one(router):
    draft = router.route("分析 a", today=date(2026, 6, 15))

    assert draft.intent == "analysis"
    assert draft.symbols == []
    assert len(draft.candidate_groups) == 1
    assert draft.candidate_groups[0].query == "a"
    assert {candidate.ticker for candidate in draft.candidate_groups[0].candidates}.issuperset({"AAPL", "AMZN"})
    assert draft.requires_confirmation is False
    assert "select" in draft.message.lower()


@pytest.mark.unit
def test_route_lists_unresolved_entities_separately(router):
    draft = router.route("比较 NVDA 和 Neverland Robotics", today=date(2026, 6, 15))

    assert draft.intent == "clarify"
    assert [symbol.ticker for symbol in draft.symbols] == ["NVDA"]
    assert draft.unresolved_entities == ["Neverland Robotics"]
    assert draft.requires_confirmation is False
    assert "more information" in draft.message.lower()


@pytest.mark.unit
def test_route_clarifies_unknown_vague_request(router):
    draft = router.route("看看那个增长还可以的公司", today=date(2026, 6, 15))

    assert draft.intent == "clarify"
    assert draft.symbols == []
    assert draft.unresolved_entities
    assert draft.requires_confirmation is False
    assert "ticker" in draft.message.lower()
