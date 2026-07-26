import numpy as np
import pandas as pd
import pytest

from portfolio.analytics import PortfolioAnalyticsEngine
from portfolio.parser import PortfolioParser
from portfolio.types import HoldingPosition


def _price_frame() -> pd.DataFrame:
    generator = np.random.default_rng(17)
    returns = generator.normal(
        [0.0005, 0.00035, 0.0004],
        [0.012, 0.009, 0.014],
        (320, 3),
    )
    return pd.DataFrame(
        100 * np.cumprod(1 + returns, axis=0),
        index=pd.date_range("2024-01-01", periods=320, freq="B"),
        columns=["AAPL", "MSFT", "JNJ"],
    )


def test_csv_parser_accepts_common_aliases_and_percent_weights() -> None:
    parsed = PortfolioParser().parse_csv(
        "Symbol,Allocation,Avg Cost\nAAPL,60%,150\nMSFT,40%,300\n"
    )
    assert [item.ticker for item in parsed] == ["AAPL", "MSFT"]
    assert parsed[0].weight == pytest.approx(0.60)
    assert parsed[1].average_cost == pytest.approx(300)


def test_csv_parser_rejects_mixed_allocation_modes() -> None:
    with pytest.raises(ValueError, match="weights for every holding"):
        PortfolioParser().parse_csv(
            "ticker,quantity,weight\nAAPL,10,\nMSFT,,50\n"
        )


def test_portfolio_analysis_outputs_frontier_and_risk_contribution() -> None:
    positions = [
        HoldingPosition("AAPL", weight=0.40),
        HoldingPosition("MSFT", weight=0.35),
        HoldingPosition("JNJ", weight=0.25),
    ]
    metadata = {
        "AAPL": {"sector": "Technology", "country": "US", "marketCap": 3e12},
        "MSFT": {"sector": "Technology", "country": "US", "marketCap": 3e12},
        "JNJ": {"sector": "Healthcare", "country": "US", "marketCap": 4e11},
    }
    result = PortfolioAnalyticsEngine().analyze(
        positions, _price_frame(), metadata
    )

    assert 0 <= result.metrics.portfolio_score <= 100
    assert 0 <= result.metrics.diversification_score <= 100
    assert len(result.efficient_frontier) >= 10
    assert sum(item.risk_contribution for item in result.holdings) == pytest.approx(
        1.0, abs=1e-4
    )
    assert result.monte_carlo.simulations == 2500
    assert result.correlation_matrix.tickers == ("AAPL", "MSFT", "JNJ")
