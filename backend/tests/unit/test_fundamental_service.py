import pytest

from fundamentals.service import FundamentalService


def test_finnhub_percentage_and_market_cap_units_are_normalized() -> None:
    metrics = FundamentalService().from_provider_data(
        {},
        {
            "revenueGrowthTTMYoy": 1.2,
            "dividendYieldIndicatedAnnual": 0.335,
            "marketCapitalization": 4_891_183.5,
        },
    )

    assert metrics.revenue_growth == pytest.approx(0.012)
    assert metrics.dividend_yield == pytest.approx(0.00335)
    assert metrics.market_cap == pytest.approx(4_891_183_500_000)


def test_yahoo_decimal_and_market_cap_units_take_precedence() -> None:
    metrics = FundamentalService().from_provider_data(
        {
            "revenueGrowth": 0.08,
            "dividendYield": 0.006,
            "marketCap": 3_000_000_000,
        },
        {
            "revenueGrowthTTMYoy": 12.0,
            "dividendYieldIndicatedAnnual": 2.0,
            "marketCapitalization": 5_000.0,
        },
    )

    assert metrics.revenue_growth == pytest.approx(0.08)
    assert metrics.dividend_yield == pytest.approx(0.006)
    assert metrics.market_cap == pytest.approx(3_000_000_000)

