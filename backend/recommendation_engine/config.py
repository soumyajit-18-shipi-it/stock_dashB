"""Named, configurable recommendation thresholds and component weights."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from core.config import settings


DEFAULT_WEIGHTS = {
    "technical": 0.24,
    "fundamental": 0.22,
    "valuation": 0.14,
    "sentiment": 0.12,
    "risk": 0.16,
    "prediction": 0.12,
}


@dataclass(frozen=True)
class DecisionConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    buy_score: float = 65.0
    sell_score: float = 35.0
    minimum_confidence: float = 0.45
    minimum_coverage: float = 0.50
    minimum_positive_non_prediction_components: int = 2
    maximum_buy_risk_score: float = -0.65
    strength_threshold: float = 0.15
    weakness_threshold: float = -0.15
    investment_horizon: str = "3-12 months"

    @classmethod
    def from_settings(cls) -> "DecisionConfig":
        if not settings.RECOMMENDATION_WEIGHTS_JSON.strip():
            return cls()
        try:
            overrides = json.loads(settings.RECOMMENDATION_WEIGHTS_JSON)
        except json.JSONDecodeError as exc:
            raise ValueError("RECOMMENDATION_WEIGHTS_JSON is not valid JSON") from exc
        weights = dict(DEFAULT_WEIGHTS)
        for name, value in overrides.items():
            if name not in weights:
                raise ValueError(f"Unknown recommendation component: {name}")
            parsed = float(value)
            if parsed < 0:
                raise ValueError("Recommendation weights cannot be negative")
            weights[name] = parsed
        if sum(weights.values()) <= 0:
            raise ValueError("At least one recommendation weight must be positive")
        return cls(weights=weights)


@dataclass(frozen=True)
class TechnicalScoreConfig:
    rsi_center: float = 50.0
    rsi_scale: float = 18.0
    rsi_overbought: float = 75.0
    rsi_oversold: float = 25.0
    adx_trending: float = 20.0
    trend_weight: float = 0.35
    momentum_weight: float = 0.25
    volume_weight: float = 0.20
    price_structure_weight: float = 0.20


@dataclass(frozen=True)
class FundamentalScoreConfig:
    growth_target: float = 0.15
    roe_target: float = 0.15
    roa_target: float = 0.07
    margin_target: float = 0.15
    current_ratio_target: float = 1.5
    debt_to_equity_limit: float = 1.5
    fcf_yield_target: float = 0.05


@dataclass(frozen=True)
class ValuationScoreConfig:
    pe_fair: float = 20.0
    pe_expensive: float = 40.0
    peg_fair: float = 1.5
    pb_fair: float = 3.0
    dividend_yield_target: float = 0.03
    fcf_yield_target: float = 0.05


@dataclass(frozen=True)
class PredictionScoreConfig:
    material_return: float = 0.03
    uncertainty_penalty_scale: float = 0.10


@dataclass(frozen=True)
class RiskScoreConfig:
    volatility_ceiling: float = 0.50
    drawdown_ceiling: float = 0.50
    value_at_risk_ceiling: float = 0.05
    minimum_observations: int = 126
    material_drawdown: float = 0.20
    elevated_liquidity_risk: float = 0.60
    strong_sharpe_ratio: float = 1.0


SECTOR_ETFS = {
    "Basic Materials": "XLB",
    "Communication Services": "XLC",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Real Estate": "XLRE",
    "Technology": "XLK",
    "Utilities": "XLU",
}

INVESTOR_PROFILES = {
    "conservative": {
        "multipliers": {
            "technical": 0.80,
            "fundamental": 1.10,
            "valuation": 1.05,
            "sentiment": 0.75,
            "risk": 1.45,
            "prediction": 0.65,
        },
        "maximum_buy_risk_score": -0.20,
        "minimum_confidence": 0.55,
    },
    "balanced": {
        "multipliers": {name: 1.0 for name in DEFAULT_WEIGHTS},
        "maximum_buy_risk_score": -0.65,
        "minimum_confidence": 0.45,
    },
    "aggressive": {
        "multipliers": {
            "technical": 1.15,
            "fundamental": 0.95,
            "valuation": 0.90,
            "sentiment": 1.10,
            "risk": 0.75,
            "prediction": 1.20,
        },
        "maximum_buy_risk_score": -0.85,
        "minimum_confidence": 0.40,
    },
}

HORIZON_LABELS = {
    "short": "1-3 months",
    "medium": "3-12 months",
    "long": "1-5 years",
}


def personalize_decision_config(
    base: DecisionConfig,
    risk_tolerance: str,
    horizon: str,
) -> DecisionConfig:
    profile = INVESTOR_PROFILES.get(risk_tolerance, INVESTOR_PROFILES["balanced"])
    weighted = {
        name: value * profile["multipliers"][name]
        for name, value in base.weights.items()
    }
    total = sum(weighted.values())
    normalized = {name: value / total for name, value in weighted.items()}
    return DecisionConfig(
        weights=normalized,
        buy_score=base.buy_score,
        sell_score=base.sell_score,
        minimum_confidence=float(profile["minimum_confidence"]),
        minimum_coverage=base.minimum_coverage,
        minimum_positive_non_prediction_components=(
            base.minimum_positive_non_prediction_components
        ),
        maximum_buy_risk_score=float(profile["maximum_buy_risk_score"]),
        strength_threshold=base.strength_threshold,
        weakness_threshold=base.weakness_threshold,
        investment_horizon=HORIZON_LABELS.get(
            horizon, HORIZON_LABELS["medium"]
        ),
    )
