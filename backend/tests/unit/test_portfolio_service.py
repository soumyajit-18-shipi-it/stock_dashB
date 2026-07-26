from portfolio.service import PortfolioService
from services.metadata_service import ProviderResult


def test_metadata_enrichment_uses_finnhub_industry_as_sector_fallback() -> None:
    enriched = PortfolioService._enrich_company_info(
        {},
        ProviderResult(
            industry="Technology",
            country="US",
            market_cap=3_000_000_000_000,
        ),
    )

    assert enriched == {
        "sector": "Technology",
        "country": "US",
        "marketCap": 3_000_000_000_000,
    }

