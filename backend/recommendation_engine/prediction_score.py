"""ML prediction component with uncertainty-aware confidence."""

from __future__ import annotations

import numpy as np

from explainability import ExplanationResult
from recommendation_engine.config import PredictionScoreConfig
from recommendation_engine.types import ScoreResult, bounded_confidence, bounded_score
from schemas import PredictionResult


class PredictionScorer:
    def __init__(self, config: PredictionScoreConfig | None = None) -> None:
        self.config = config or PredictionScoreConfig()

    def calculate(
        self,
        prediction: PredictionResult,
        current_price: float,
        explanation: ExplanationResult | None,
    ) -> ScoreResult:
        if current_price <= 0:
            return ScoreResult(0.0, 0.0, "Current price is unavailable")
        expected_return = (
            prediction.predicted_price - current_price
        ) / current_price
        score = float(np.tanh(expected_return / self.config.material_return))
        interval_width = 0.0
        uncertainty_penalty = 1.0
        metrics: dict[str, float | str | None] = {
            "predicted_price": prediction.predicted_price,
            "current_price": current_price,
            "expected_return": expected_return,
            "model": prediction.model_used,
        }
        if explanation is not None:
            interval_width = (
                explanation.uncertainty_upper - explanation.uncertainty_lower
            ) / current_price
            uncertainty_penalty = 1.0 / (
                1.0 + interval_width / self.config.uncertainty_penalty_scale
            )
            metrics.update(
                {
                    "uncertainty_lower": explanation.uncertainty_lower,
                    "uncertainty_upper": explanation.uncertainty_upper,
                    "explanation_method": explanation.method,
                }
            )
        confidence = prediction.confidence * uncertainty_penalty
        reason = (
            f"Model-implied return is {expected_return * 100:.1f}% "
            f"with {interval_width * 100:.1f}% interval width"
        )
        return ScoreResult(
            score=round(bounded_score(score), 6),
            confidence=round(bounded_confidence(confidence), 6),
            reason=reason,
            evidence=(reason,),
            metrics=metrics,
        )
