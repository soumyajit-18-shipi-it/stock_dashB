"""Risk-adjusted desirability component."""

from __future__ import annotations

import numpy as np

from recommendation_engine.types import ScoreResult, bounded_confidence, bounded_score
from risk import RiskMetrics


class RiskScorer:
    def calculate(self, metrics: RiskMetrics) -> ScoreResult:
        risks: dict[str, float | None] = {
            "volatility": min(1.0, metrics.historical_volatility / 0.50),
            "drawdown": min(1.0, metrics.maximum_drawdown / 0.50),
            "value_at_risk": min(1.0, metrics.value_at_risk_95 / 0.05),
            "liquidity": metrics.liquidity_risk,
            "tail": metrics.tail_risk,
            "sector": metrics.sector_risk,
        }
        available = [value for value in risks.values() if value is not None]
        composite_risk = float(np.mean(available)) if available else 0.5
        score = bounded_score(1.0 - 2.0 * composite_risk)
        confidence = min(1.0, len(available) / len(risks)) * min(
            1.0, metrics.observations / 126.0
        )
        evidence = []
        if metrics.risk_level == "high":
            evidence.append("Overall market risk is high")
        if metrics.volatility_regime == "high":
            evidence.append("Volatility is above its recent regime")
        if metrics.maximum_drawdown >= 0.20:
            evidence.append("Historical maximum drawdown is material")
        if metrics.liquidity_risk >= 0.60:
            evidence.append("Trading liquidity may be limited")
        if metrics.sharpe_ratio > 1.0:
            evidence.append("Historical risk-adjusted returns are strong")
        if not evidence:
            evidence.append("Observed risk metrics are moderate")
        return ScoreResult(
            score=round(score, 6),
            confidence=round(bounded_confidence(confidence), 6),
            reason=evidence[0],
            evidence=tuple(evidence[:4]),
            metrics=metrics.to_dict(),
        )
