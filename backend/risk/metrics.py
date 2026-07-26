"""Reusable market and portfolio risk metrics.

Return-based statistics use daily observations and 252 trading days per year.
Loss statistics are reported as positive magnitudes, which keeps API consumers
from having to infer sign conventions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RiskConfig:
    trading_days: int = 252
    var_confidence: float = 0.95
    short_window: int = 21
    regime_window: int = 63
    high_regime_ratio: float = 1.30
    low_regime_ratio: float = 0.75
    high_volatility: float = 0.40
    medium_volatility: float = 0.25
    high_drawdown: float = 0.35
    medium_drawdown: float = 0.20
    liquid_daily_value: float = 20_000_000.0
    illiquid_daily_value: float = 1_000_000.0


@dataclass(frozen=True)
class RiskMetrics:
    historical_volatility: float
    sharpe_ratio: float
    beta: float | None
    maximum_drawdown: float
    value_at_risk_95: float
    expected_shortfall_95: float
    sortino_ratio: float
    volatility_regime: str
    volatility_regime_ratio: float
    liquidity_risk: float
    tail_risk: float
    sector_risk: float | None
    risk_level: str
    observations: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RiskCalculator:
    def __init__(
        self, risk_free_rate: float = 0.04, config: RiskConfig | None = None
    ) -> None:
        self.risk_free_rate = risk_free_rate
        self.config = config or RiskConfig()

    def calculate(
        self,
        prices: pd.Series,
        volumes: pd.Series | None = None,
        benchmark_prices: pd.Series | None = None,
        sector_prices: pd.Series | None = None,
    ) -> RiskMetrics:
        prices = pd.to_numeric(prices, errors="coerce").dropna()
        returns = prices.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        if len(returns) < 2:
            raise ValueError("At least three valid prices are required for risk metrics")

        annual_factor = self.config.trading_days
        annual_return = float(returns.mean() * annual_factor)
        annual_volatility = float(
            returns.std(ddof=1) * np.sqrt(annual_factor)
        )
        excess_return = annual_return - self.risk_free_rate
        sharpe = (
            excess_return / annual_volatility if annual_volatility > 0 else 0.0
        )

        downside = returns[returns < 0]
        downside_deviation = float(
            downside.std(ddof=1) * np.sqrt(annual_factor)
        ) if len(downside) > 1 else 0.0
        sortino = excess_return / downside_deviation if downside_deviation > 0 else 0.0

        wealth = (1.0 + returns).cumprod()
        drawdown = wealth / wealth.cummax() - 1.0
        maximum_drawdown = float(abs(drawdown.min()))

        loss_quantile = float(returns.quantile(1.0 - self.config.var_confidence))
        value_at_risk = max(0.0, -loss_quantile)
        tail = returns[returns <= loss_quantile]
        expected_shortfall = max(
            0.0, -float(tail.mean()) if not tail.empty else value_at_risk
        )

        beta = self._beta(returns, benchmark_prices)
        regime, regime_ratio = self._volatility_regime(returns)
        liquidity_risk = self._liquidity_risk(prices, volumes)
        daily_volatility = float(returns.std(ddof=1))
        tail_risk = min(
            1.0,
            expected_shortfall / max(daily_volatility * 3.0, np.finfo(float).eps),
        )
        sector_risk = self._sector_risk(sector_prices, benchmark_prices)
        level = self._risk_level(annual_volatility, maximum_drawdown, tail_risk)

        return RiskMetrics(
            historical_volatility=round(annual_volatility, 6),
            sharpe_ratio=round(float(sharpe), 6),
            beta=round(beta, 6) if beta is not None else None,
            maximum_drawdown=round(maximum_drawdown, 6),
            value_at_risk_95=round(value_at_risk, 6),
            expected_shortfall_95=round(expected_shortfall, 6),
            sortino_ratio=round(float(sortino), 6),
            volatility_regime=regime,
            volatility_regime_ratio=round(regime_ratio, 6),
            liquidity_risk=round(liquidity_risk, 6),
            tail_risk=round(tail_risk, 6),
            sector_risk=round(sector_risk, 6)
            if sector_risk is not None
            else None,
            risk_level=level,
            observations=len(returns),
        )

    def _beta(
        self, returns: pd.Series, benchmark_prices: pd.Series | None
    ) -> float | None:
        if benchmark_prices is None:
            return None
        benchmark = (
            pd.to_numeric(benchmark_prices, errors="coerce")
            .pct_change()
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )
        aligned = pd.concat(
            [returns.rename("asset"), benchmark.rename("benchmark")],
            axis=1,
            join="inner",
        ).dropna()
        if len(aligned) < 20:
            return None
        variance = float(aligned["benchmark"].var(ddof=1))
        if variance <= 0:
            return None
        return float(aligned.cov().loc["asset", "benchmark"] / variance)

    def _volatility_regime(self, returns: pd.Series) -> tuple[str, float]:
        rolling = returns.rolling(
            self.config.short_window, min_periods=self.config.short_window
        ).std(ddof=1)
        current = float(rolling.iloc[-1]) if pd.notna(rolling.iloc[-1]) else 0.0
        baseline = float(
            rolling.tail(self.config.regime_window).median()
        )
        if baseline <= 0:
            return "normal", 1.0
        ratio = current / baseline
        if ratio >= self.config.high_regime_ratio:
            return "high", ratio
        if ratio <= self.config.low_regime_ratio:
            return "low", ratio
        return "normal", ratio

    def _liquidity_risk(
        self, prices: pd.Series, volumes: pd.Series | None
    ) -> float:
        if volumes is None:
            return 0.5
        aligned = pd.concat(
            [
                prices.rename("price"),
                pd.to_numeric(volumes, errors="coerce").rename("volume"),
            ],
            axis=1,
            join="inner",
        ).dropna()
        if aligned.empty:
            return 0.5
        median_daily_value = float(
            (aligned["price"] * aligned["volume"]).tail(20).median()
        )
        low = self.config.illiquid_daily_value
        high = self.config.liquid_daily_value
        if median_daily_value <= low:
            return 1.0
        if median_daily_value >= high:
            return 0.0
        log_position = (
            np.log(median_daily_value) - np.log(low)
        ) / (np.log(high) - np.log(low))
        return float(1.0 - log_position)

    def _sector_risk(
        self,
        sector_prices: pd.Series | None,
        benchmark_prices: pd.Series | None,
    ) -> float | None:
        if sector_prices is None or benchmark_prices is None:
            return None
        sector_returns = pd.to_numeric(
            sector_prices, errors="coerce"
        ).pct_change()
        benchmark_returns = pd.to_numeric(
            benchmark_prices, errors="coerce"
        ).pct_change()
        aligned = pd.concat(
            [sector_returns.rename("sector"), benchmark_returns.rename("market")],
            axis=1,
        ).dropna()
        if len(aligned) < 20:
            return None
        sector_vol = float(aligned["sector"].std(ddof=1))
        market_vol = float(aligned["market"].std(ddof=1))
        if market_vol <= 0:
            return None
        volatility_ratio = sector_vol / market_vol
        correlation = float(aligned["sector"].corr(aligned["market"]))
        return float(
            np.clip(
                0.65 * ((volatility_ratio - 0.75) / 1.0)
                + 0.35 * max(correlation, 0.0),
                0.0,
                1.0,
            )
        )

    def _risk_level(
        self, annual_volatility: float, maximum_drawdown: float, tail_risk: float
    ) -> str:
        high_flags = sum(
            (
                annual_volatility >= self.config.high_volatility,
                maximum_drawdown >= self.config.high_drawdown,
                tail_risk >= 0.75,
            )
        )
        medium_flags = sum(
            (
                annual_volatility >= self.config.medium_volatility,
                maximum_drawdown >= self.config.medium_drawdown,
                tail_risk >= 0.50,
            )
        )
        if high_flags >= 1 or medium_flags >= 2:
            return "high"
        if medium_flags >= 1:
            return "medium"
        return "low"
