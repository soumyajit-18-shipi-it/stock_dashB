import numpy as np
import pandas as pd

from risk import RiskCalculator


def test_risk_metrics_are_finite_and_use_positive_loss_magnitudes() -> None:
    generator = np.random.default_rng(11)
    returns = generator.normal(0.0004, 0.012, 300)
    benchmark_returns = generator.normal(0.0003, 0.009, 300)
    index = pd.date_range("2024-01-01", periods=300, freq="B")
    prices = pd.Series(100 * np.cumprod(1 + returns), index=index)
    benchmark = pd.Series(
        100 * np.cumprod(1 + benchmark_returns), index=index
    )
    volumes = pd.Series(2_000_000, index=index)

    result = RiskCalculator(0.04).calculate(
        prices, volumes, benchmark
    )

    assert result.historical_volatility > 0
    assert result.maximum_drawdown >= 0
    assert result.value_at_risk_95 >= 0
    assert result.expected_shortfall_95 >= result.value_at_risk_95
    assert result.beta is not None
    assert result.risk_level in {"low", "medium", "high"}


def test_risk_metrics_require_enough_prices() -> None:
    with np.testing.assert_raises(ValueError):
        RiskCalculator().calculate(pd.Series([100.0, 101.0]))
