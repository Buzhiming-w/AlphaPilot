from datetime import date

import pytest

from alphapilot.backend.security_master.resolver import SecurityMasterResolver
from alphapilot.backend.security_master.seed import seed_initial_security_master
from alphapilot.backend.security_master.sync import sync_security_master_from_texts
from alphapilot.backend.sqlalchemy_store import SqlAlchemyAlphaPilotStore
from alphapilot.backend.workflow_router import WorkflowRouter


NASDAQ_LISTED_FIXTURE = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
ORCL|Oracle Corporation Common Stock|Q|N|N|100|N|N
File Creation Time: 0615202600:00|||||||
"""


OTHER_LISTED_FIXTURE = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
MMM|3M Company Common Stock|N|MMM|N|100|N|MMM
SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY
File Creation Time: 0615202600:00|||||||
"""


SEC_TICKERS_FIXTURE = """{
  "fields": ["cik", "name", "ticker", "exchange"],
  "data": [
    [1341439, "Oracle Corporation", "ORCL", "Nasdaq"],
    [66740, "3M Company", "MMM", "NYSE"]
  ]
}"""


@pytest.fixture()
def store(tmp_path):
    return SqlAlchemyAlphaPilotStore(database_url=f"sqlite:///{tmp_path / 'security_master.db'}")


@pytest.mark.unit
def test_security_master_sync_loads_nasdaq_sec_fixtures_and_is_idempotent(store):
    first = sync_security_master_from_texts(
        store,
        nasdaq_listed_text=NASDAQ_LISTED_FIXTURE,
        other_listed_text=OTHER_LISTED_FIXTURE,
        sec_tickers_json=SEC_TICKERS_FIXTURE,
    )
    second = sync_security_master_from_texts(
        store,
        nasdaq_listed_text=NASDAQ_LISTED_FIXTURE,
        other_listed_text=OTHER_LISTED_FIXTURE,
        sec_tickers_json=SEC_TICKERS_FIXTURE,
    )

    resolver = SecurityMasterResolver(store)
    assert first.status == "completed"
    assert second.status == "completed"
    assert resolver.search("ORCL")[0].company_name == "Oracle Corporation"
    assert resolver.search("3M")[0].ticker == "MMM"
    assert resolver.search("SPY")[0].ticker == "SPY"


@pytest.mark.unit
def test_security_master_resolves_chinese_names_and_person_aliases_from_database(store):
    seed_initial_security_master(store)
    resolver = SecurityMasterResolver(store)

    assert resolver.search("甲骨文")[0].ticker == "ORCL"
    assert resolver.search("黄仁勋")[0].ticker == "NVDA"
    assert resolver.search("巴菲特的公司")[0].ticker == "BRK.B"


@pytest.mark.unit
def test_workflow_router_uses_security_master_for_3m_orcl_compare(store, monkeypatch):
    monkeypatch.setenv("ALPHAPILOT_COPILOT_LLM_ENABLED", "false")
    sync_security_master_from_texts(
        store,
        nasdaq_listed_text=NASDAQ_LISTED_FIXTURE,
        other_listed_text=OTHER_LISTED_FIXTURE,
        sec_tickers_json=SEC_TICKERS_FIXTURE,
    )
    router = WorkflowRouter(directory=SecurityMasterResolver(store))

    draft = router.route("比较3M和orcl两只股票的表现，从2015年6月至今", today=date(2026, 6, 15))

    assert draft.intent == "compare"
    assert [symbol.ticker for symbol in draft.symbols] == ["MMM", "ORCL"]
    assert draft.start_date == "2015-06-01"
    assert draft.end_date == "2026-06-15"
