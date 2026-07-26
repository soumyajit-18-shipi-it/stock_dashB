"""Repeatable CPU benchmark for deterministic investment analytics."""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from features.technical_indicators import TechnicalIndicators  # noqa: E402
from portfolio.analytics import PortfolioAnalyticsEngine  # noqa: E402
from portfolio.types import HoldingPosition  # noqa: E402
from recommendation_engine.config import DecisionConfig  # noqa: E402
from recommendation_engine.decision_engine import DecisionEngine  # noqa: E402
from recommendation_engine.types import ScoreResult  # noqa: E402
from risk import RiskCalculator  # noqa: E402


def _measure(function: Callable[[], object], repetitions: int) -> dict[str, float]:
    durations = []
    for _ in range(repetitions):
        start = time.perf_counter()
        function()
        durations.append((time.perf_counter() - start) * 1000.0)
    return {
        "median_ms": round(statistics.median(durations), 3),
        "p95_ms": round(float(np.percentile(durations, 95)), 3),
        "repetitions": repetitions,
    }


def main() -> None:
    generator = np.random.default_rng(42)
    dates = pd.date_range("2021-01-01", periods=1_260, freq="B")
    asset_returns = generator.normal(
        [0.00045, 0.00035, 0.00030, 0.00040, 0.00025],
        [0.012, 0.010, 0.009, 0.014, 0.011],
        (len(dates), 5),
    )
    tickers = ["AAPL", "MSFT", "JNJ", "XOM", "JPM"]
    closes = 100 * np.cumprod(1 + asset_returns, axis=0)
    price_frame = pd.DataFrame(closes, index=dates, columns=tickers)
    ohlcv = pd.DataFrame(
        {
            "Open": price_frame["AAPL"] * 0.998,
            "High": price_frame["AAPL"] * 1.01,
            "Low": price_frame["AAPL"] * 0.99,
            "Close": price_frame["AAPL"],
            "Volume": generator.integers(1_000_000, 8_000_000, len(dates)),
        },
        index=dates,
    )
    positions = [
        HoldingPosition(ticker, weight=weight)
        for ticker, weight in zip(tickers, [0.25, 0.25, 0.20, 0.15, 0.15])
    ]
    metadata = {
        ticker: {
            "sector": sector,
            "country": "US",
            "marketCap": market_cap,
            "returnOnEquity": roe,
        }
        for ticker, sector, market_cap, roe in zip(
            tickers,
            ["Technology", "Technology", "Healthcare", "Energy", "Financial Services"],
            [3e12, 3e12, 4e11, 5e11, 6e11],
            [0.30, 0.28, 0.20, 0.18, 0.16],
        )
    }
    component = ScoreResult(0.4, 0.8, "benchmark")
    components = {
        name: component
        for name in (
            "technical",
            "fundamental",
            "valuation",
            "sentiment",
            "risk",
            "prediction",
        )
    }

    results = {
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "assets": len(tickers),
            "observations": len(dates),
        },
        "technical_indicators": _measure(
            lambda: TechnicalIndicators.add_all_indicators(ohlcv), 50
        ),
        "risk_metrics": _measure(
            lambda: RiskCalculator().calculate(
                ohlcv["Close"], ohlcv["Volume"], price_frame["MSFT"]
            ),
            100,
        ),
        "decision_engine": _measure(
            lambda: DecisionEngine(DecisionConfig()).decide(
                components, "medium", 0.04, -0.05
            ),
            2_000,
        ),
        "portfolio_analysis": _measure(
            lambda: PortfolioAnalyticsEngine().analyze(
                positions, price_frame, metadata, price_frame["MSFT"]
            ),
            5,
        ),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
