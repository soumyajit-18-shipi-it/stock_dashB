"""Weighted deterministic decision policy; no LLM participates here."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from recommendation_engine.config import DecisionConfig
from recommendation_engine.types import ScoreResult


@dataclass(frozen=True)
class DecisionResult:
    recommendation: str
    overall_score: float
    confidence: float
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    risk_level: str
    expected_return: float
    expected_downside: float
    investment_horizon: str
    components: dict[str, dict[str, Any]]
    policy_checks: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DecisionEngine:
    def __init__(self, config: DecisionConfig | None = None) -> None:
        self.config = config or DecisionConfig.from_settings()

    def decide(
        self,
        components: dict[str, ScoreResult],
        risk_level: str,
        expected_return: float,
        expected_downside: float,
    ) -> DecisionResult:
        configured_weight = sum(self.config.weights.values())
        effective_weight = sum(
            self.config.weights.get(name, 0.0) * component.confidence
            for name, component in components.items()
        )
        weighted_signal = sum(
            self.config.weights.get(name, 0.0)
            * component.confidence
            * component.score
            for name, component in components.items()
        )
        score = (
            weighted_signal / effective_weight if effective_weight > 0 else 0.0
        )
        overall_score = (score + 1.0) * 50.0
        coverage = (
            effective_weight / configured_weight if configured_weight > 0 else 0.0
        )
        active = [
            component.score
            for component in components.values()
            if component.confidence > 0
        ]
        dispersion = float(np.std(active)) if len(active) > 1 else 1.0
        agreement = max(0.0, 1.0 - dispersion / 1.0)
        confidence = coverage * (0.65 + 0.35 * agreement)

        positive_non_prediction = sum(
            component.score >= self.config.strength_threshold
            and component.confidence > 0
            for name, component in components.items()
            if name != "prediction"
        )
        risk_score = components.get("risk", ScoreResult(0.0, 0.0, "")).score
        checks = {
            "minimum_confidence": confidence >= self.config.minimum_confidence,
            "minimum_coverage": coverage >= self.config.minimum_coverage,
            "diverse_buy_evidence": (
                positive_non_prediction
                >= self.config.minimum_positive_non_prediction_components
            ),
            "buy_risk_guard": risk_score >= self.config.maximum_buy_risk_score,
        }
        if (
            overall_score >= self.config.buy_score
            and all(checks.values())
        ):
            recommendation = "BUY"
        elif (
            overall_score <= self.config.sell_score
            and checks["minimum_confidence"]
            and checks["minimum_coverage"]
        ):
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        strengths = self._collect(
            components, positive=True, threshold=self.config.strength_threshold
        )
        weaknesses = self._collect(
            components, positive=False, threshold=self.config.weakness_threshold
        )
        return DecisionResult(
            recommendation=recommendation,
            overall_score=round(overall_score, 4),
            confidence=round(max(0.0, min(1.0, confidence)), 6),
            strengths=tuple(strengths),
            weaknesses=tuple(weaknesses),
            risk_level=risk_level,
            expected_return=round(expected_return, 6),
            expected_downside=round(expected_downside, 6),
            investment_horizon=self.config.investment_horizon,
            components={
                name: {
                    **component.to_dict(),
                    "weight": self.config.weights.get(name, 0.0),
                    "contribution": round(
                        self.config.weights.get(name, 0.0)
                        * component.confidence
                        * component.score,
                        6,
                    ),
                }
                for name, component in components.items()
            },
            policy_checks=checks,
        )

    @staticmethod
    def _collect(
        components: dict[str, ScoreResult],
        *,
        positive: bool,
        threshold: float,
    ) -> list[str]:
        ranked = sorted(
            components.items(),
            key=lambda item: abs(item[1].score * item[1].confidence),
            reverse=True,
        )
        result: list[str] = []
        for _, component in ranked:
            passes = (
                component.score >= threshold
                if positive
                else component.score <= threshold
            )
            if not passes:
                continue
            candidates = component.evidence or (component.reason,)
            for candidate in candidates:
                if candidate and candidate not in result:
                    result.append(candidate)
                if len(result) >= 5:
                    return result
        return result
