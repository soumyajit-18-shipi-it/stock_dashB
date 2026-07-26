"""Public API schemas for portfolio workflows."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PortfolioHoldingInput(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    quantity: float | None = Field(default=None, gt=0)
    average_cost: float | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, gt=0, le=1)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def require_position(self) -> "PortfolioHoldingInput":
        if self.quantity is None and self.weight is None:
            raise ValueError("quantity or weight is required")
        return self


class PortfolioAnalyzeRequest(BaseModel):
    holdings: list[PortfolioHoldingInput] = Field(min_length=1, max_length=30)
    range: Literal["1y", "5y"] = "5y"

    @model_validator(mode="after")
    def consistent_allocation_mode(self) -> "PortfolioAnalyzeRequest":
        weighted = [item.weight is not None for item in self.holdings]
        if any(weighted) and not all(weighted):
            raise ValueError("provide weights for every holding or quantities for all")
        tickers = [item.ticker for item in self.holdings]
        if len(tickers) != len(set(tickers)):
            raise ValueError("portfolio tickers must be unique")
        return self


class PortfolioCsvRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1_000_000)


class PortfolioCsvResponse(BaseModel):
    holdings: list[PortfolioHoldingInput]


class HoldingSnapshotSchema(BaseModel):
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


class PortfolioMetricsSchema(BaseModel):
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


class CorrelationMatrixSchema(BaseModel):
    tickers: list[str]
    values: list[list[float]]


class FrontierPointSchema(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


class MonteCarloSchema(BaseModel):
    simulations: int
    horizon_days: int
    expected_terminal_value: float
    percentile_5: float
    percentile_50: float
    percentile_95: float
    loss_probability: float


class RebalanceActionSchema(BaseModel):
    ticker: str
    current_weight: float
    target_weight: float
    change: float
    action: str


class AllocationPointSchema(BaseModel):
    date: str
    weights: dict[str, float]


class PortfolioAnalysisResponse(BaseModel):
    generated_at: str
    metrics: PortfolioMetricsSchema
    holdings: list[HoldingSnapshotSchema]
    sector_exposure: dict[str, float]
    country_exposure: dict[str, float]
    market_cap_exposure: dict[str, float]
    factor_exposure: dict[str, float]
    correlation_matrix: CorrelationMatrixSchema
    efficient_frontier: list[FrontierPointSchema]
    monte_carlo: MonteCarloSchema
    rebalancing: list[RebalanceActionSchema]
    allocation_timeline: list[AllocationPointSchema]
    largest_risks: list[str]
    weakest_holdings: list[str]
    best_holdings: list[str]
    explanation: list[str]
    data_warnings: list[str]


class PortfolioExplainRequest(BaseModel):
    analysis: PortfolioAnalysisResponse


class PortfolioExplanationResponse(BaseModel):
    explanation: str
    source: str = "llm"
    deterministic_scores_unchanged: bool = True


class PortfolioJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    result: PortfolioAnalysisResponse | None = None
    error: str | None = None


class PortfolioSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    holdings: list[PortfolioHoldingInput] = Field(min_length=1, max_length=30)
    analysis_snapshot: PortfolioAnalysisResponse | None = None


class SavedPortfolioResponse(BaseModel):
    id: str
    user_id: str
    name: str
    analysis_snapshot: dict[str, Any] | None = None
    holdings: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
