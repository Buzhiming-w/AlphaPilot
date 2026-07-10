from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


EXCHANGE_NAMES = {
    "A": "NYSE American",
    "N": "NYSE",
    "P": "NYSE Arca",
    "Q": "NASDAQ",
    "V": "IEX",
    "Z": "Cboe BZX",
}


def _clean_name(name: str) -> str:
    suffixes = (
        " Common Stock",
        " Ordinary Shares",
        " Class A Common Stock",
        " Class B Common Stock",
    )
    cleaned = name.strip()
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
    return cleaned.strip()


def _parse_pipe_rows(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter="|")
    rows: list[dict[str, str]] = []
    for row in reader:
        first_value = next(iter(row.values()), "")
        if str(first_value).startswith("File Creation Time"):
            continue
        rows.append({str(key): str(value or "").strip() for key, value in row.items() if key})
    return rows


def _sec_by_ticker(sec_tickers_json: str) -> dict[str, dict]:
    payload = json.loads(sec_tickers_json)
    fields = payload.get("fields", [])
    ticker_index = fields.index("ticker")
    return {
        str(row[ticker_index]).upper(): dict(zip(fields, row, strict=False))
        for row in payload.get("data", [])
    }


def _asset_type(is_etf: bool) -> str:
    return "etf" if is_etf else "stock"


def _upsert_source_row(store, *, symbol: str, name: str, exchange: str, is_etf: bool, sec_data: dict | None, raw: dict):
    security, created = store.upsert_security(
        symbol=symbol,
        name=sec_data.get("name") if sec_data and sec_data.get("name") else _clean_name(name),
        exchange=exchange,
        market="US",
        currency="USD",
        asset_type=_asset_type(is_etf),
        is_etf=is_etf,
        cik=str(sec_data.get("cik")) if sec_data and sec_data.get("cik") else None,
        status="active",
        source="nasdaq_trader",
        raw_payload=raw,
    )
    aliases = {symbol, name, _clean_name(name)}
    if sec_data and sec_data.get("name"):
        aliases.add(str(sec_data["name"]))
    for alias in aliases:
        if alias:
            store.add_security_alias(
                security_id=security.id,
                alias=alias,
                alias_type="source_name",
                source="nasdaq_sec_sync",
            )
    return created


def sync_security_master_from_texts(
    store,
    *,
    nasdaq_listed_text: str,
    other_listed_text: str,
    sec_tickers_json: str,
):
    started_at = datetime.now(timezone.utc)
    inserted = 0
    updated = 0
    try:
        sec_lookup = _sec_by_ticker(sec_tickers_json)
        for row in _parse_pipe_rows(nasdaq_listed_text):
            if row.get("Test Issue") == "Y":
                continue
            symbol = row.get("Symbol", "").upper()
            if not symbol:
                continue
            created = _upsert_source_row(
                store,
                symbol=symbol,
                name=row.get("Security Name", ""),
                exchange="NASDAQ",
                is_etf=row.get("ETF") == "Y",
                sec_data=sec_lookup.get(symbol),
                raw=row,
            )
            inserted += 1 if created else 0
            updated += 0 if created else 1
        for row in _parse_pipe_rows(other_listed_text):
            if row.get("Test Issue") == "Y":
                continue
            symbol = row.get("ACT Symbol", "").upper()
            if not symbol:
                continue
            exchange = EXCHANGE_NAMES.get(row.get("Exchange"), row.get("Exchange") or "UNKNOWN")
            created = _upsert_source_row(
                store,
                symbol=symbol,
                name=row.get("Security Name", ""),
                exchange=exchange,
                is_etf=row.get("ETF") == "Y",
                sec_data=sec_lookup.get(symbol),
                raw=row,
            )
            inserted += 1 if created else 0
            updated += 0 if created else 1
        return store.create_security_master_sync_run(
            source="nasdaq_trader_sec",
            status="completed",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            inserted_count=inserted,
            updated_count=updated,
            raw_metadata={"nasdaq_rows": inserted + updated},
        )
    except Exception as exc:
        return store.create_security_master_sync_run(
            source="nasdaq_trader_sec",
            status="failed",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            error=str(exc),
        )


def _download(url: str) -> str:
    request = Request(url, headers={"User-Agent": "AlphaPilot/0.1 contact=admin@alphapilot.dev"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def sync_security_master(store):
    return sync_security_master_from_texts(
        store,
        nasdaq_listed_text=_download(NASDAQ_LISTED_URL),
        other_listed_text=_download(OTHER_LISTED_URL),
        sec_tickers_json=_download(SEC_TICKERS_URL),
    )


if __name__ == "__main__":
    from alphapilot.backend.settings import get_database_url
    from alphapilot.backend.sqlalchemy_store import SqlAlchemyAlphaPilotStore

    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("ALPHAPILOT_DATABASE_URL is required for Security Master sync")
    run = sync_security_master(SqlAlchemyAlphaPilotStore(database_url))
    print(f"{run.status}: inserted={run.inserted_count} updated={run.updated_count}")
