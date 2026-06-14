import pytest

from alphapilot.backend.ticker_directory import LocalTickerDirectory


@pytest.fixture()
def directory():
    return LocalTickerDirectory()


@pytest.mark.unit
def test_search_matches_exact_ticker(directory):
    matches = directory.search("NVDA")

    assert matches[0].ticker == "NVDA"
    assert matches[0].company_name == "NVIDIA Corporation"
    assert matches[0].market == "US"
    assert matches[0].exchange == "NASDAQ"
    assert matches[0].currency == "USD"
    assert matches[0].confidence == "high"


@pytest.mark.unit
def test_search_matches_company_alias_chinese_name_and_person(directory):
    assert directory.search("Nvidia")[0].ticker == "NVDA"
    assert directory.search("英伟达")[0].ticker == "NVDA"
    assert directory.search("黄仁勋")[0].ticker == "NVDA"
    assert directory.search("Advanced Micro Devices")[0].ticker == "AMD"
    assert directory.search("苹果公司")[0].ticker == "AAPL"


@pytest.mark.unit
def test_search_returns_multiple_candidates_for_ambiguous_short_query(directory):
    matches = directory.search("a")
    tickers = {match.ticker for match in matches}

    assert {"AAPL", "AMZN"}.issubset(tickers)
    assert len(matches) <= 5


@pytest.mark.unit
def test_search_returns_empty_list_for_unknown_company(directory):
    assert directory.search("a private coffee shop with no ticker") == []

