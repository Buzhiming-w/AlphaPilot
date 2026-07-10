from __future__ import annotations


INITIAL_SECURITIES = (
    {
        "symbol": "MMM",
        "name": "3M Company",
        "exchange": "NYSE",
        "aliases": (
            ("3M", "company_short_name"),
            ("3M Company", "company_legal_name"),
            ("明尼苏达矿务", "chinese_name"),
            ("3M公司", "chinese_name"),
        ),
    },
    {
        "symbol": "ORCL",
        "name": "Oracle Corporation",
        "exchange": "NASDAQ",
        "aliases": (
            ("Oracle", "english_common_name"),
            ("Oracle Corporation", "company_legal_name"),
            ("甲骨文", "chinese_name"),
        ),
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "exchange": "NASDAQ",
        "aliases": (
            ("NVIDIA", "english_common_name"),
            ("英伟达", "chinese_name"),
            ("辉达", "chinese_name"),
            ("Jensen Huang", "person"),
            ("黄仁勋", "person"),
        ),
    },
    {
        "symbol": "AMD",
        "name": "Advanced Micro Devices, Inc.",
        "exchange": "NASDAQ",
        "aliases": (
            ("Advanced Micro Devices", "company_short_name"),
            ("超威半导体", "chinese_name"),
            ("Lisa Su", "person"),
            ("苏姿丰", "person"),
        ),
    },
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "aliases": (
            ("Apple", "english_common_name"),
            ("苹果", "chinese_name"),
            ("苹果公司", "chinese_name"),
            ("Tim Cook", "person"),
            ("库克", "person"),
        ),
    },
    {
        "symbol": "BRK.B",
        "name": "Berkshire Hathaway Inc.",
        "exchange": "NYSE",
        "aliases": (
            ("Berkshire Hathaway", "company_short_name"),
            ("伯克希尔", "chinese_name"),
            ("Warren Buffett", "person"),
            ("巴菲特", "person"),
            ("巴菲特的公司", "person"),
        ),
    },
)


def seed_initial_security_master(store) -> None:
    for item in INITIAL_SECURITIES:
        security, _ = store.upsert_security(
            symbol=item["symbol"],
            name=item["name"],
            exchange=item["exchange"],
            market="US",
            currency="USD",
            asset_type="stock",
            is_etf=False,
            source="seed",
            raw_payload={"seed": True},
        )
        store.add_security_alias(
            security_id=security.id,
            alias=item["symbol"],
            alias_type="ticker",
            source="seed",
        )
        store.add_security_alias(
            security_id=security.id,
            alias=item["name"],
            alias_type="company_legal_name",
            source="seed",
        )
        for alias, alias_type in item["aliases"]:
            store.add_security_alias(
                security_id=security.id,
                alias=alias,
                alias_type=alias_type,
                source="seed",
            )
