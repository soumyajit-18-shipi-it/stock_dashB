"""Valuation score kept separate from operating fundamentals."""

from __future__ import annotations

import numpy as np

from fundamentals import FundamentalMetrics
from recommendation_engine.config import ValuationScoreConfig
from recommendation_engine.types import ScoreResult, bounded_score


class ValuationScorer:
    def __init__(self, config: ValuationScoreConfig | None = None) -> None:
        self.config = config or ValuationScoreConfig()

    def calculate(self, metrics: FundamentalMetrics) -> ScoreResult:
        scores: dict[str, float | None] = {
            "P/E": self._multiple(
                metrics.pe_ratio, self.config.pe_fair, self.config.pe_expensive
            ),
            "Forward P/E": self._multiple(
                metrics.forward_pe, self.config.pe_fair, self.config.pe_expensive
            ),
            "PEG": self._multiple(
                metrics.peg_ratio, self.config.peg_fair, self.config.peg_fair * 2.0
            ),
            "Price-to-book": self._multiple(
                metrics.price_to_book, self.config.pb_fair, self.config.pb_fair * 3.0
            ),
            "Dividend yield": self._yield_score(
                metrics.dividend_yield, self.config.dividend_yield_target
            ),
            "Free cash flow yield": self._yield_score(
                metrics.free_cash_flow_yield, self.config.fcf_yield_target
            ),
        }
        available = {name: value for name, value in scores.items() if value is not None}
        if not available:
            return ScoreResult(0.0, 0.0, "Valuation data is unavailable")
        score = float(np.mean(list(available.values())))
        confidence = min(0.90, len(available) / len(scores))
        ranked = sorted(available.items(), key=lambda item: abs(item[1]), reverse=True)
        evidence = tuple(
            f"{name} looks {'attractive' if value > 0 else 'expensive'}"
            for name, value in ranked[:3]
            if abs(value) >= 0.15
        )
        return ScoreResult(
            score=round(bounded_score(score), 6),
            confidence=round(confidence, 6),
            reason=evidence[0] if evidence else "Valuation is near configured fair ranges",
            evidence=evidence,
            metrics={
                "pe_ratio": metrics.pe_ratio,
                "forward_pe": metrics.forward_pe,
                "peg_ratio": metrics.peg_ratio,
                "price_to_book": metrics.price_to_book,
                "dividend_yield": metrics.dividend_yield,
                "free_cash_flow_yield": metrics.free_cash_flow_yield,
            },
        )

    @staticmethod
    def _multiple(
        value: float | None, fair: float, expensive: float
    ) -> float | None:
        if value is None:
            return None
        if value <= 0:
            return -1.0
        return float(np.clip((expensive - value) / (expensive - fair) - 1.0, -1.0, 1.0))

    @staticmethod
    def _yield_score(value: float | None, target: float) -> float | None:
        if value is None or target == 0:
            return None
        return float(np.clip(value / target - 0.5, -1.0, 1.0))
