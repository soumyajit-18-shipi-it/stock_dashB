"""Pure portfolio allocation, risk, optimization, and simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from portfolio.types import (
    AllocationPoint,
    CorrelationMatrix,
    FrontierPoint,
    HoldingPosition,
    HoldingSnapshot,
    MonteCarloSummary,
    PortfolioAnalysis,
    PortfolioMetrics,
    RebalanceAction,
)
from risk import RiskCalculator


@dataclass(frozen=True)
class PortfolioAnalyticsConfig:
    trading_days: int = 252
    minimum_observations: int = 60
    max_holdings: int = 30
    max_target_weight: float = 0.35
    frontier_points: int = 18
    monte_carlo_simulations: int = 2500
    monte_carlo_days: int = 252
    monte_carlo_seed: int = 42
    expected_return_floor: float = -0.50
    expected_return_ceiling: float = 1.00
    volatility_risk_limit: float = 0.40
    drawdown_risk_limit: float = 0.40
    rebalancing_materiality: float = 0.02


class PortfolioAnalyticsEngine:
    def __init__(
        self,
        risk_free_rate: float = 0.04,
        config: PortfolioAnalyticsConfig | None = None,
    ) -> None:
        self.config = config or PortfolioAnalyticsConfig()
        self.risk_free_rate = risk_free_rate
        self.risk_calculator = RiskCalculator(risk_free_rate)

    def analyze(
        self,
        positions: list[HoldingPosition],
        prices: pd.DataFrame,
        metadata: dict[str, dict[str, object]],
        benchmark_prices: pd.Series | None = None,
        warnings: list[str] | None = None,
    ) -> PortfolioAnalysis:
        if not positions:
            raise ValueError("At least one holding is required")
        if len(positions) > self.config.max_holdings:
            raise ValueError(
                f"Portfolio exceeds the {self.config.max_holdings}-holding limit"
            )
        tickers = [position.ticker for position in positions]
        clean_prices = (
            prices.loc[:, tickers]
            .apply(pd.to_numeric, errors="coerce")
            .sort_index()
            .ffill()
            .dropna()
        )
        if len(clean_prices) < self.config.minimum_observations:
            raise ValueError(
                "Insufficient overlapping price history for portfolio analysis"
            )
        returns = clean_prices.pct_change().dropna()
        latest_prices = clean_prices.iloc[-1]
        weights, market_values = self._weights(
            positions, latest_prices
        )

        expected_asset_returns = self._expected_asset_returns(returns)
        covariance = LedoitWolf().fit(returns.to_numpy(dtype=float)).covariance_
        covariance = covariance * self.config.trading_days
        portfolio_returns = returns.dot(weights)
        expected_return = float(expected_asset_returns @ weights)
        expected_volatility = float(
            np.sqrt(max(weights @ covariance @ weights, 0.0))
        )
        risk_metrics = self.risk_calculator.calculate(
            (1.0 + portfolio_returns).cumprod(),
            benchmark_prices=benchmark_prices,
        )
        risk_contribution = self._risk_contribution(weights, covariance)
        correlation = returns.corr()
        exposures = self._exposures(tickers, weights, metadata)
        holding_rows = self._holding_rows(
            positions,
            latest_prices,
            market_values,
            weights,
            returns,
            risk_contribution,
            metadata,
        )
        diversification_score, effective_holdings, hhi = self._diversification_score(
            weights, correlation, exposures["sector"]
        )
        risk_score = self._risk_score(
            expected_volatility, risk_metrics.maximum_drawdown
        )
        return_quality = float(
            np.clip(50.0 + risk_metrics.sharpe_ratio * 18.0, 0.0, 100.0)
        )
        portfolio_score = (
            0.40 * diversification_score
            + 0.35 * risk_score
            + 0.25 * return_quality
        )
        frontier, target_weights = self._efficient_frontier(
            tickers, expected_asset_returns, covariance
        )
        monte_carlo = self._monte_carlo(portfolio_returns)
        rebalancing = self._rebalancing(
            tickers, weights, target_weights
        )
        timeline = self._allocation_timeline(clean_prices, weights)
        factor_exposure = self._factor_exposure(
            returns, weights, metadata, benchmark_prices
        )
        largest_risks = self._largest_risks(
            holding_rows,
            exposures["sector"],
            expected_volatility,
            risk_metrics.maximum_drawdown,
        )
        ranked = sorted(
            holding_rows, key=lambda item: item.holding_score, reverse=True
        )
        explanation = self._explanation(
            diversification_score,
            expected_volatility,
            exposures["sector"],
            rebalancing,
        )

        return PortfolioAnalysis(
            generated_at=datetime.now(timezone.utc).isoformat(),
            metrics=PortfolioMetrics(
                portfolio_score=round(portfolio_score, 4),
                diversification_score=round(diversification_score, 4),
                risk_score=round(risk_score, 4),
                expected_return=round(expected_return, 6),
                expected_volatility=round(expected_volatility, 6),
                sharpe_ratio=round(risk_metrics.sharpe_ratio, 6),
                sortino_ratio=round(risk_metrics.sortino_ratio, 6),
                maximum_drawdown=round(risk_metrics.maximum_drawdown, 6),
                value_at_risk_95=round(risk_metrics.value_at_risk_95, 6),
                beta=risk_metrics.beta,
                effective_holdings=round(effective_holdings, 4),
                concentration_hhi=round(hhi, 6),
            ),
            holdings=tuple(holding_rows),
            sector_exposure=exposures["sector"],
            country_exposure=exposures["country"],
            market_cap_exposure=exposures["market_cap"],
            factor_exposure=factor_exposure,
            correlation_matrix=CorrelationMatrix(
                tickers=tuple(tickers),
                values=tuple(
                    tuple(round(float(value), 6) for value in row)
                    for row in correlation.loc[tickers, tickers].to_numpy()
                ),
            ),
            efficient_frontier=tuple(frontier),
            monte_carlo=monte_carlo,
            rebalancing=tuple(rebalancing),
            allocation_timeline=tuple(timeline),
            largest_risks=tuple(largest_risks),
            weakest_holdings=tuple(item.ticker for item in ranked[-3:]),
            best_holdings=tuple(item.ticker for item in ranked[:3]),
            explanation=tuple(explanation),
            data_warnings=tuple(warnings or []),
        )

    def _weights(
        self,
        positions: list[HoldingPosition],
        latest_prices: pd.Series,
    ) -> tuple[np.ndarray, np.ndarray]:
        supplied_weights = [item.weight for item in positions]
        if all(value is not None for value in supplied_weights):
            weights = np.asarray(supplied_weights, dtype=float)
            market_values = weights.copy()
        elif any(value is not None for value in supplied_weights):
            raise ValueError("Provide weights for every holding or for none")
        else:
            quantities = np.asarray(
                [item.quantity or 0.0 for item in positions], dtype=float
            )
            if np.any(quantities <= 0):
                raise ValueError("Every holding requires a positive quantity")
            market_values = quantities * latest_prices.to_numpy(dtype=float)
            weights = market_values.copy()
        total = float(weights.sum())
        if total <= 0:
            raise ValueError("Portfolio value or allocation must be positive")
        return weights / total, market_values

    def _expected_asset_returns(self, returns: pd.DataFrame) -> np.ndarray:
        ewma = (
            returns.ewm(span=126, adjust=False).mean().iloc[-1]
            * self.config.trading_days
        )
        return np.clip(
            ewma.to_numpy(dtype=float),
            self.config.expected_return_floor,
            self.config.expected_return_ceiling,
        )

    @staticmethod
    def _risk_contribution(
        weights: np.ndarray, covariance: np.ndarray
    ) -> np.ndarray:
        variance = float(weights @ covariance @ weights)
        if variance <= 0:
            return np.zeros_like(weights)
        marginal = covariance @ weights
        contribution = weights * marginal / variance
        return contribution

    def _holding_rows(
        self,
        positions: list[HoldingPosition],
        latest_prices: pd.Series,
        market_values: np.ndarray,
        weights: np.ndarray,
        returns: pd.DataFrame,
        risk_contribution: np.ndarray,
        metadata: dict[str, dict[str, object]],
    ) -> list[HoldingSnapshot]:
        rows: list[HoldingSnapshot] = []
        for index, position in enumerate(positions):
            series = returns[position.ticker]
            annual_return = float(
                (1.0 + series).prod()
                ** (self.config.trading_days / max(len(series), 1))
                - 1.0
            )
            annual_volatility = float(
                series.std(ddof=1) * np.sqrt(self.config.trading_days)
            )
            score = float(
                np.clip(
                    50.0
                    + 40.0 * annual_return
                    - 25.0 * annual_volatility,
                    0.0,
                    100.0,
                )
            )
            info = metadata.get(position.ticker, {})
            market_cap = self._number(info.get("marketCap"))
            rows.append(
                HoldingSnapshot(
                    ticker=position.ticker,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    current_price=round(float(latest_prices[position.ticker]), 6),
                    market_value=round(float(market_values[index]), 6),
                    weight=round(float(weights[index]), 6),
                    annual_return=round(annual_return, 6),
                    annual_volatility=round(annual_volatility, 6),
                    risk_contribution=round(float(risk_contribution[index]), 6),
                    sector=str(info.get("sector") or "Unknown"),
                    country=str(info.get("country") or "Unknown"),
                    market_cap_bucket=self._market_cap_bucket(market_cap),
                    holding_score=round(score, 4),
                )
            )
        return rows

    def _exposures(
        self,
        tickers: list[str],
        weights: np.ndarray,
        metadata: dict[str, dict[str, object]],
    ) -> dict[str, dict[str, float]]:
        output = {"sector": {}, "country": {}, "market_cap": {}}
        for ticker, weight in zip(tickers, weights):
            info = metadata.get(ticker, {})
            keys = {
                "sector": str(info.get("sector") or "Unknown"),
                "country": str(info.get("country") or "Unknown"),
                "market_cap": self._market_cap_bucket(
                    self._number(info.get("marketCap"))
                ),
            }
            for exposure, key in keys.items():
                output[exposure][key] = output[exposure].get(key, 0.0) + float(weight)
        return {
            name: {
                key: round(value, 6)
                for key, value in sorted(
                    values.items(), key=lambda item: item[1], reverse=True
                )
            }
            for name, values in output.items()
        }

    def _diversification_score(
        self,
        weights: np.ndarray,
        correlation: pd.DataFrame,
        sector_exposure: dict[str, float],
    ) -> tuple[float, float, float]:
        effective_holdings = 1.0 / float(np.sum(weights**2))
        breadth = effective_holdings / len(weights)
        if len(weights) > 1:
            matrix = correlation.to_numpy(dtype=float)
            average_correlation = float(
                matrix[np.triu_indices_from(matrix, k=1)].mean()
            )
        else:
            average_correlation = 1.0
        correlation_quality = float(np.clip((1.0 - average_correlation) / 1.5, 0.0, 1.0))
        hhi = sum(value**2 for value in sector_exposure.values())
        sector_quality = float(np.clip((1.0 - hhi) / 0.75, 0.0, 1.0))
        score = 100.0 * (
            0.45 * breadth + 0.30 * correlation_quality + 0.25 * sector_quality
        )
        return score, effective_holdings, hhi

    def _risk_score(self, volatility: float, drawdown: float) -> float:
        composite = 0.55 * min(
            1.0, volatility / self.config.volatility_risk_limit
        ) + 0.45 * min(1.0, drawdown / self.config.drawdown_risk_limit)
        return 100.0 * (1.0 - composite)

    def _efficient_frontier(
        self,
        tickers: list[str],
        expected_returns: np.ndarray,
        covariance: np.ndarray,
    ) -> tuple[list[FrontierPoint], np.ndarray]:
        count = len(tickers)
        maximum_weight = max(self.config.max_target_weight, 1.0 / count)
        bounds = [(0.0, maximum_weight) for _ in range(count)]
        initial = np.repeat(1.0 / count, count)

        def volatility(weights: np.ndarray) -> float:
            return float(np.sqrt(max(weights @ covariance @ weights, 0.0)))

        def negative_sharpe(weights: np.ndarray) -> float:
            vol = volatility(weights)
            if vol <= 0:
                return 1e6
            return -float(
                (expected_returns @ weights - self.risk_free_rate) / vol
            )

        constraints = [{"type": "eq", "fun": lambda weights: weights.sum() - 1.0}]
        optimal = minimize(
            negative_sharpe,
            initial,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 400, "ftol": 1e-10},
        )
        target_weights = (
            optimal.x if optimal.success else initial
        )
        frontier: list[FrontierPoint] = []
        minimum_return = float(
            expected_returns
            @ self._extreme_return_weights(
                expected_returns, maximum_weight, maximize=False
            )
        )
        maximum_return = float(
            expected_returns
            @ self._extreme_return_weights(
                expected_returns, maximum_weight, maximize=True
            )
        )
        targets = np.linspace(
            minimum_return,
            maximum_return,
            self.config.frontier_points,
        )
        for target in targets:
            target_constraints = [
                constraints[0],
                {
                    "type": "eq",
                    "fun": lambda weights, target_return=target: (
                        expected_returns @ weights - target_return
                    ),
                },
            ]
            result = minimize(
                volatility,
                initial,
                method="SLSQP",
                bounds=bounds,
                constraints=target_constraints,
                options={"maxiter": 300, "ftol": 1e-9},
            )
            if not result.success:
                continue
            point_return = float(expected_returns @ result.x)
            point_volatility = volatility(result.x)
            frontier.append(
                FrontierPoint(
                    expected_return=round(point_return, 6),
                    volatility=round(point_volatility, 6),
                    sharpe_ratio=round(
                        (point_return - self.risk_free_rate)
                        / point_volatility
                        if point_volatility > 0
                        else 0.0,
                        6,
                    ),
                    weights={
                        ticker: round(float(weight), 6)
                        for ticker, weight in zip(tickers, result.x)
                    },
                )
            )
        return frontier, target_weights

    @staticmethod
    def _extreme_return_weights(
        expected_returns: np.ndarray,
        maximum_weight: float,
        *,
        maximize: bool,
    ) -> np.ndarray:
        order = np.argsort(expected_returns)
        if maximize:
            order = order[::-1]
        weights = np.zeros(len(expected_returns), dtype=float)
        remaining = 1.0
        for index in order:
            allocation = min(maximum_weight, remaining)
            weights[index] = allocation
            remaining -= allocation
            if remaining <= 1e-12:
                break
        return weights

    def _monte_carlo(self, portfolio_returns: pd.Series) -> MonteCarloSummary:
        generator = np.random.default_rng(self.config.monte_carlo_seed)
        daily_mean = float(portfolio_returns.mean())
        daily_volatility = float(portfolio_returns.std(ddof=1))
        simulated = generator.normal(
            daily_mean,
            daily_volatility,
            (
                self.config.monte_carlo_simulations,
                self.config.monte_carlo_days,
            ),
        )
        terminal = np.prod(1.0 + simulated, axis=1)
        percentiles = np.percentile(terminal, [5, 50, 95])
        return MonteCarloSummary(
            simulations=self.config.monte_carlo_simulations,
            horizon_days=self.config.monte_carlo_days,
            expected_terminal_value=round(float(np.mean(terminal)), 6),
            percentile_5=round(float(percentiles[0]), 6),
            percentile_50=round(float(percentiles[1]), 6),
            percentile_95=round(float(percentiles[2]), 6),
            loss_probability=round(float(np.mean(terminal < 1.0)), 6),
        )

    def _rebalancing(
        self,
        tickers: list[str],
        current: np.ndarray,
        target: np.ndarray,
    ) -> list[RebalanceAction]:
        actions = []
        for ticker, current_weight, target_weight in zip(tickers, current, target):
            change = float(target_weight - current_weight)
            if abs(change) < self.config.rebalancing_materiality:
                action = "HOLD"
            else:
                action = "INCREASE" if change > 0 else "REDUCE"
            actions.append(
                RebalanceAction(
                    ticker=ticker,
                    current_weight=round(float(current_weight), 6),
                    target_weight=round(float(target_weight), 6),
                    change=round(change, 6),
                    action=action,
                )
            )
        return sorted(actions, key=lambda item: abs(item.change), reverse=True)

    def _allocation_timeline(
        self, prices: pd.DataFrame, initial_weights: np.ndarray
    ) -> list[AllocationPoint]:
        sample = prices.tail(self.config.trading_days).iloc[::21]
        if sample.empty:
            return []
        normalized = sample / sample.iloc[0]
        values = normalized.mul(initial_weights, axis=1)
        weights = values.div(values.sum(axis=1), axis=0)
        return [
            AllocationPoint(
                date=index.date().isoformat()
                if hasattr(index, "date")
                else str(index),
                weights={
                    ticker: round(float(value), 6)
                    for ticker, value in row.items()
                },
            )
            for index, row in weights.iterrows()
        ]

    def _factor_exposure(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        metadata: dict[str, dict[str, object]],
        benchmark_prices: pd.Series | None,
    ) -> dict[str, float]:
        annual_volatility = returns.std(ddof=1).to_numpy() * np.sqrt(
            self.config.trading_days
        )
        momentum = (
            (1.0 + returns.tail(126)).prod().to_numpy(dtype=float) - 1.0
        )
        beta = np.ones(len(weights))
        if benchmark_prices is not None:
            benchmark = pd.to_numeric(
                benchmark_prices, errors="coerce"
            ).pct_change().dropna()
            for index, ticker in enumerate(returns.columns):
                aligned = pd.concat(
                    [returns[ticker], benchmark], axis=1
                ).dropna()
                if len(aligned) >= 20:
                    variance = float(aligned.iloc[:, 1].var(ddof=1))
                    if variance > 0:
                        beta[index] = float(
                            aligned.cov().iloc[0, 1] / variance
                        )
        size_scores = []
        quality_scores = []
        for ticker in returns.columns:
            info = metadata.get(ticker, {})
            cap = self._number(info.get("marketCap"))
            size_scores.append(
                1.0 if cap and cap >= 10e9 else 0.0 if cap and cap >= 2e9 else -1.0
            )
            roe = self._number(info.get("returnOnEquity"))
            quality_scores.append(float(np.tanh((roe or 0.0) / 0.15)))
        return {
            "market_beta": round(float(weights @ beta), 6),
            "momentum": round(float(weights @ momentum), 6),
            "volatility": round(float(weights @ annual_volatility), 6),
            "large_cap_tilt": round(float(weights @ np.asarray(size_scores)), 6),
            "quality": round(float(weights @ np.asarray(quality_scores)), 6),
        }

    def _largest_risks(
        self,
        holdings: list[HoldingSnapshot],
        sectors: dict[str, float],
        volatility: float,
        drawdown: float,
    ) -> list[str]:
        risks: list[tuple[float, str]] = []
        top_holding = max(holdings, key=lambda item: item.weight)
        risks.append(
            (
                top_holding.weight,
                f"{top_holding.ticker} is {top_holding.weight * 100:.1f}% of the portfolio",
            )
        )
        if sectors:
            sector, weight = max(sectors.items(), key=lambda item: item[1])
            risks.append(
                (weight, f"{sector} sector exposure is {weight * 100:.1f}%")
            )
        risks.append(
            (volatility, f"Expected annual volatility is {volatility * 100:.1f}%")
        )
        risks.append(
            (drawdown, f"Historical maximum drawdown is {drawdown * 100:.1f}%")
        )
        top_risk = max(holdings, key=lambda item: item.risk_contribution)
        risks.append(
            (
                top_risk.risk_contribution,
                f"{top_risk.ticker} contributes {top_risk.risk_contribution * 100:.1f}% of variance",
            )
        )
        return [text for _, text in sorted(risks, reverse=True)[:5]]

    def _explanation(
        self,
        diversification_score: float,
        volatility: float,
        sectors: dict[str, float],
        rebalancing: list[RebalanceAction],
    ) -> list[str]:
        statements = [
            (
                f"Diversification scores {diversification_score:.0f}/100 "
                "after accounting for weights, correlations, and sectors."
            ),
            (
                f"The return history implies {volatility * 100:.1f}% "
                "annualized volatility."
            ),
        ]
        if sectors:
            sector, weight = max(sectors.items(), key=lambda item: item[1])
            statements.append(
                f"The largest sector allocation is {sector} at {weight * 100:.1f}%."
            )
        material = [item for item in rebalancing if item.action != "HOLD"]
        if material:
            statements.append(
                f"{len(material)} holdings have allocation changes above the "
                f"{self.config.rebalancing_materiality * 100:.0f}% materiality threshold."
            )
        return statements

    @staticmethod
    def _market_cap_bucket(value: float | None) -> str:
        if value is None:
            return "Unknown"
        if value >= 10e9:
            return "Large cap"
        if value >= 2e9:
            return "Mid cap"
        if value >= 300e6:
            return "Small cap"
        return "Micro cap"

    @staticmethod
    def _number(value: object) -> float | None:
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return parsed if parsed == parsed else None
