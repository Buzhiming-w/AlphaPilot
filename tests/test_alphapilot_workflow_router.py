from datetime import date

import pytest

from alphapilot.backend.workflow_router import WorkflowRouter


@pytest.fixture()
def router():
    return WorkflowRouter()


@pytest.mark.unit
def test_route_multi_compare_with_person_company_and_date_range(router):
    draft = router.route("帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在", today=date(2026, 6, 15))

    assert draft.intent == "multi_compare"
    assert [symbol.ticker for symbol in draft.symbols] == ["NVDA", "AMD"]
    assert draft.start_date == "2024-01-01"
    assert draft.end_date == "2026-06-15"
    assert draft.analysis_anchor == "2026-06-15"
    assert draft.requires_confirmation is True


@pytest.mark.unit
def test_route_watchlist_addition_from_chinese_company_name(router):
    draft = router.route("把苹果加入股票池", today=date(2026, 6, 15))

    assert draft.intent == "add_to_watchlist"
    assert [symbol.ticker for symbol in draft.symbols] == ["AAPL"]
    assert draft.requires_confirmation is True


@pytest.mark.unit
def test_route_single_analysis_with_iso_date(router):
    draft = router.route("研究英伟达 2024-05-10", today=date(2026, 6, 15))

    assert draft.intent == "single_analysis"
    assert [symbol.ticker for symbol in draft.symbols] == ["NVDA"]
    assert draft.start_date is None
    assert draft.end_date == "2024-05-10"
    assert draft.analysis_anchor == "2024-05-10"


@pytest.mark.unit
def test_route_clarifies_unknown_vague_request(router):
    draft = router.route("看看那个增长还可以的公司", today=date(2026, 6, 15))

    assert draft.intent == "clarify"
    assert draft.symbols == []
    assert draft.requires_confirmation is False
    assert "ticker" in draft.message.lower()

