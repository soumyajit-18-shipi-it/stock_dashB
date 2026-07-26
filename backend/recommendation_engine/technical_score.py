"""Technical component score built from the canonical indicator frame."""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.technical_indicators import TechnicalIndicators
from recommendation_engine.config import TechnicalScoreConfig
from recommendation_engine.types import ScoreResult, bounded_confidence, bounded_score


class TechnicalScorer:
    def __init__(self, config: TechnicalScoreConfig | None = None) -> None:
        self.config = config or TechnicalScoreConfig()
        self.indicators = TechnicalIndicators()

    def calculate(self, history: pd.DataFrame) -> ScoreResult:
        frame = self.indicators.add_all_indicators(history)
        if frame.empty:
            return ScoreResult(0.0, 0.0, "Technical history is unavailable")
        row = frame.iloc[-1]
        close = self._value(row, "Close")
        atr = self._value(row, "atr_14")

        signals: dict[str, float | None] = {
            "ema_trend": self._relative_signal(
                self._value(row, "ema_20"),
                self._value(row, "ema_50"),
                atr,
            ),
            "macd": self._scaled_signal(
                self._value(row, "macd_histogram"), atr
            ),
            "cloud": self._cloud_signal(
                close,
                self._value(row, "ichimoku_span_a_current"),
                self._value(row, "ichimoku_span_b_current"),
            ),
            "rsi": self._rsi_signal(self._value(row, "rsi_14")),
            "stochastic": self._centered(
                self._value(row, "stoch_rsi_k"), 50.0, 35.0
            ),
            "momentum": self._scaled_signal(
                self._value(row, "momentum_20"), 0.10
            ),
            "obv": self._scaled_signal(
                self._value(row, "obv_slope_20"), 0.25
            ),
            "volume": self._scaled_signal(
                self._value(row, "volume_confirmation"), 2.0
            ),
            "vwap": self._relative_signal(
                close, self._value(row, "vwap"), atr
            ),
            "bollinger": self._centered(
                self._value(row, "bollinger_percent_b"), 0.5, 0.5
            ),
        }
        groups = {
            "trend": self._mean(signals["ema_trend"], signals["macd"], signals["cloud"]),
            "momentum": self._mean(
                signals["rsi"], signals["stochastic"], signals["momentum"]
            ),
            "volume": self._mean(signals["obv"], signals["volume"]),
            "price_structure": self._mean(signals["vwap"], signals["bollinger"]),
        }
        weights = {
            "trend": self.config.trend_weight,
            "momentum": self.config.momentum_weight,
            "volume": self.config.volume_weight,
            "price_structure": self.config.price_structure_weight,
        }
        available = {
            key: value for key, value in groups.items() if value is not None
        }
        if not available:
            return ScoreResult(0.0, 0.0, "Indicators have insufficient warm-up data")
        denominator = sum(weights[key] for key in available)
        score = sum(weights[key] * value for key, value in available.items()) / denominator
        adx = self._value(row, "adx_14")
        adx_confidence = (
            min(1.0, adx / self.config.adx_trending)
            if adx is not None
            else 0.5
        )
        warmup_coverage = min(1.0, len(frame) / 100.0)
        confidence = len(available) / len(groups) * (
            0.65 + 0.35 * adx_confidence
        ) * warmup_coverage
        evidence = self._evidence(row, groups, adx)
        reason = (
            evidence[0]
            if evidence
            else "Technical signals are balanced"
        )
        return ScoreResult(
            score=round(bounded_score(score), 6),
            confidence=round(bounded_confidence(confidence), 6),
            reason=reason,
            evidence=tuple(evidence),
            metrics={
                "rsi": self._rounded(self._value(row, "rsi_14")),
                "macd_histogram": self._rounded(
                    self._value(row, "macd_histogram")
                ),
                "adx": self._rounded(adx),
                "atr": self._rounded(atr),
                "support": self._rounded(self._value(row, "support_20")),
                "resistance": self._rounded(
                    self._value(row, "resistance_20")
                ),
                "groups": {
                    key: round(value, 6) if value is not None else None
                    for key, value in groups.items()
                },
            },
        )

    def _rsi_signal(self, value: float | None) -> float | None:
        if value is None:
            return None
        if value >= self.config.rsi_overbought:
            return -min(1.0, (value - self.config.rsi_overbought) / 15.0)
        if value <= self.config.rsi_oversold:
            return min(1.0, (self.config.rsi_oversold - value) / 15.0)
        return float(
            np.clip(
                (value - self.config.rsi_center) / self.config.rsi_scale,
                -1.0,
                1.0,
            )
        )

    @staticmethod
    def _value(row: pd.Series, key: str) -> float | None:
        value = row.get(key)
        if value is None or not pd.notna(value):
            return None
        return float(value)

    @staticmethod
    def _scaled_signal(value: float | None, scale: float | None) -> float | None:
        if value is None or scale is None or scale == 0:
            return None
        return float(np.tanh(value / scale))

    @staticmethod
    def _relative_signal(
        first: float | None, second: float | None, scale: float | None
    ) -> float | None:
        if first is None or second is None or scale is None or scale == 0:
            return None
        return float(np.tanh((first - second) / scale))

    @staticmethod
    def _centered(
        value: float | None, center: float, scale: float
    ) -> float | None:
        if value is None:
            return None
        return float(np.clip((value - center) / scale, -1.0, 1.0))

    @staticmethod
    def _cloud_signal(
        close: float | None, span_a: float | None, span_b: float | None
    ) -> float | None:
        if close is None or span_a is None or span_b is None:
            return None
        upper, lower = max(span_a, span_b), min(span_a, span_b)
        if close > upper:
            return 1.0
        if close < lower:
            return -1.0
        return 0.0

    @staticmethod
    def _mean(*values: float | None) -> float | None:
        available = [value for value in values if value is not None]
        return float(np.mean(available)) if available else None

    @staticmethod
    def _rounded(value: float | None) -> float | None:
        return round(value, 6) if value is not None else None

    def _evidence(
        self,
        row: pd.Series,
        groups: dict[str, float | None],
        adx: float | None,
    ) -> list[str]:
        candidates: list[tuple[float, str]] = []
        labels = {
            "trend": ("Price trend is constructive", "Price trend is weakening"),
            "momentum": ("Momentum is positive", "Momentum is negative"),
            "volume": ("Volume confirms the move", "Volume does not confirm the move"),
            "price_structure": (
                "Price structure supports further upside",
                "Price structure shows downside pressure",
            ),
        }
        for key, value in groups.items():
            if value is None or abs(value) < 0.15:
                continue
            text = labels[key][0 if value > 0 else 1]
            candidates.append((abs(value), text))
        rsi = self._value(row, "rsi_14")
        if rsi is not None and rsi >= self.config.rsi_overbought:
            candidates.append((1.0, "RSI is overbought"))
        elif rsi is not None and rsi <= self.config.rsi_oversold:
            candidates.append((1.0, "RSI is recovering from oversold conditions"))
        if adx is not None and adx >= self.config.adx_trending:
            candidates.append((min(adx / 50.0, 1.0), "ADX confirms an established trend"))
        return [text for _, text in sorted(candidates, reverse=True)[:4]]
