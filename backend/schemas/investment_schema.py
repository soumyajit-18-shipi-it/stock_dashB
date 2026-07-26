"""Public API schemas for recommendations and prediction explanations."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class InvestmentHorizon(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ComponentScore(BaseModel):
    score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    reason: str
    evidence: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(ge=0)
    contribution: float


class ExplanationFeatureSchema(BaseModel):
    feature: str
    display_name: str
    value: float
    contribution: float
    direction: str
    importance_percent: float = Field(ge=0, le=100)


class PredictionExplanationResponse(BaseModel):
    ticker: str
    model: str
    method: str
    provider_status: str
    base_value: float
    predicted_price: float
    current_price: float
    expected_return: float
    confidence: float = Field(ge=0, le=1)
    uncertainty_lower: float
    uncertainty_upper: float
    features: list[ExplanationFeatureSchema]
    additivity_residual: float


class DecisionResponse(BaseModel):
    recommendation: str
    overall_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    strengths: list[str]
    weaknesses: list[str]
    risk_level: str
    expected_return: float
    expected_downside: float
    investment_horizon: str
    components: dict[str, ComponentScore]
    policy_checks: dict[str, bool]


class RecommendationResponse(BaseModel):
    ticker: str
    generated_at: str
    risk_tolerance: str
    decision: DecisionResponse
    prediction_explanation: PredictionExplanationResponse | None = None


class RecommendationExplainRequest(BaseModel):
    recommendation: RecommendationResponse


class RecommendationExplanationResponse(BaseModel):
    explanation: str
    source: str = "llm"
    deterministic_decision_unchanged: bool = True
