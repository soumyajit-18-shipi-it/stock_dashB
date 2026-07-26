from services.metadata_service import MetadataService, ProviderResult


def test_yahoo_metadata_includes_country() -> None:
    service = MetadataService()

    result = service._try_yahoo(
        "AAPL",
        {
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "United States",
            "marketCap": 3_000_000_000_000,
        },
        ProviderResult(),
    )

    assert result.sector == "Technology"
    assert result.country == "United States"
    assert result.market_cap == 3_000_000_000_000
    assert "country" in service.last_diagnostics[-1].fields_returned

