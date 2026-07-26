"""Typed internal portfolio analysis contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HoldingPosition:
    ticker: str
    quantity: float | None = None
    average_cost: float | None = None
    weight: float | None = None


@dataclass(frozen=True)
class HoldingSnapshot:
    ticker: str
    quantity: float | None
    average_cost: float | None
    current_price: float
    market_value: float
    weight: float
    annual_return: float
    annual_volatility: float
    risk_contribution: float
    sector: str
    country: str
    market_cap_bucket: str
    holding_score: float


@dataclass(frozen=True)
class PortfolioMetrics:
    portfolio_score: float
    diversification_score: float
    risk_score: float
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    maximum_drawdown: float
    value_at_risk_95: float
    beta: float | None
    effective_holdings: float
    concentration_hhi: float


@dataclass(frozen=True)
class CorrelationMatrix:
    tickers: tuple[str, ...]
    values: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class FrontierPoint:
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


@dataclass(frozen=True)
class MonteCarloSummary:
    simulations: int
    horizon_days: int
    expected_terminal_value: float
    percentile_5: float
    percentile_50: float
    percentile_95: float
    loss_probability: float


@dataclass(frozen=True)
class RebalanceAction:
    ticker: str
    current_weight: float
    target_weight: float
    change: float
    action: str


@dataclass(frozen=True)
class AllocationPoint:
    date: str
    weights: dict[str, float]


@dataclass(frozen=True)
class PortfolioAnalysis:
    generated_at: str
    metrics: PortfolioMetrics
    holdings: tuple[HoldingSnapshot, ...]
    sector_exposure: dict[str, float]
    country_exposure: dict[str, float]
    market_cap_exposure: dict[str, float]
    factor_exposure: dict[str, float]
    correlation_matrix: CorrelationMatrix
    efficient_frontier: tuple[FrontierPoint, ...]
    monte_carlo: MonteCarloSummary
    rebalancing: tuple[RebalanceAction, ...]
    allocation_timeline: tuple[AllocationPoint, ...]
    largest_risks: tuple[str, ...]
    weakest_holdings: tuple[str, ...]
    best_holdings: tuple[str, ...]
    explanation: tuple[str, ...]
    data_warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
