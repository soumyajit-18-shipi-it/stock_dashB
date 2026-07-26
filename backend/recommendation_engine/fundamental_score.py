"""Business quality, growth, balance-sheet, and cash-flow score."""

from __future__ import annotations

import numpy as np

from fundamentals import FundamentalMetrics
from recommendation_engine.config import FundamentalScoreConfig
from recommendation_engine.types import ScoreResult, bounded_confidence, bounded_score


class FundamentalScorer:
    def __init__(self, config: FundamentalScoreConfig | None = None) -> None:
        self.config = config or FundamentalScoreConfig()

    def calculate(self, metrics: FundamentalMetrics) -> ScoreResult:
        values: dict[str, float | None] = {
            "Revenue growth": self._scaled(metrics.revenue_growth, self.config.growth_target),
            "EPS growth": self._scaled(metrics.eps_growth, self.config.growth_target),
            "Return on equity": self._scaled(metrics.return_on_equity, self.config.roe_target),
            "Return on assets": self._scaled(metrics.return_on_assets, self.config.roa_target),
            "Operating margin": self._scaled(metrics.operating_margin, self.config.margin_target),
            "Profit margin": self._scaled(metrics.profit_margin, self.config.margin_target),
            "Current ratio": self._centered(metrics.current_ratio, self.config.current_ratio_target),
            "Quick ratio": self._centered(metrics.quick_ratio, 1.0),
            "Debt load": self._inverse(metrics.debt_to_equity, self.config.debt_to_equity_limit),
            "Free cash flow yield": self._scaled(
                metrics.free_cash_flow_yield, self.config.fcf_yield_target
            ),
        }
        available = {key: value for key, value in values.items() if value is not None}
        if not available:
            return ScoreResult(0.0, 0.0, "Fundamental data is unavailable")
        score = float(np.mean(list(available.values())))
        confidence = metrics.source_coverage * min(1.0, len(available) / 7.0)
        ranked = sorted(available.items(), key=lambda item: abs(item[1]), reverse=True)
        evidence = tuple(
            f"{name} is {'strong' if value > 0 else 'weak'}"
            for name, value in ranked[:4]
            if abs(value) >= 0.15
        )
        return ScoreResult(
            score=round(bounded_score(score), 6),
            confidence=round(bounded_confidence(confidence), 6),
            reason=evidence[0] if evidence else "Fundamental signals are balanced",
            evidence=evidence,
            metrics=metrics.to_dict(),
        )

    @staticmethod
    def _scaled(value: float | None, target: float) -> float | None:
        return float(np.tanh(value / target)) if value is not None and target else None

    @staticmethod
    def _centered(value: float | None, target: float) -> float | None:
        if value is None or target == 0:
            return None
        return float(np.clip((value - 1.0) / target, -1.0, 1.0))

    @staticmethod
    def _inverse(value: float | None, limit: float) -> float | None:
        if value is None or limit == 0:
            return None
        return float(np.clip((limit - value) / limit, -1.0, 1.0))
