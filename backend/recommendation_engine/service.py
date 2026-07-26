"""Orchestrate market evidence into a deterministic recommendation."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from core.config import settings
from explainability import ExplanationResult, PredictionExplanationService
from fundamentals import FundamentalService
from recommendation_engine.config import (
    DecisionConfig,
    SECTOR_ETFS,
    personalize_decision_config,
)
from recommendation_engine.decision_engine import DecisionEngine, DecisionResult
from recommendation_engine.fundamental_score import FundamentalScorer
from recommendation_engine.prediction_score import PredictionScorer
from recommendation_engine.risk_score import RiskScorer
from recommendation_engine.sentiment_score import SentimentScorer
from recommendation_engine.technical_score import TechnicalScorer
from recommendation_engine.valuation_score import ValuationScorer
from risk import RiskCalculator, RiskMetrics
from schemas import DateRangeEnum, ModelEnum
from sentiment import SentimentService
from services.stock_service import StockService
from services.ai_service import AIService, ai_service


@dataclass(frozen=True)
class RecommendationResult:
    ticker: str
    generated_at: str
    risk_tolerance: str
    decision: DecisionResult
    prediction_explanation: ExplanationResult | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.to_dict()
        data["prediction_explanation"] = (
            self.prediction_explanation.to_dict()
            if self.prediction_explanation is not None
            else None
        )
        return data


class RecommendationService:
    def __init__(
        self,
        stock_service: StockService | None = None,
        explanation_service: AIService | None = None,
    ) -> None:
        self.stock_service = stock_service or StockService()
        provider = self.stock_service.data_provider
        predictor = self.stock_service.predictor
        self.fundamentals = FundamentalService(provider)
        self.sentiment = SentimentService()
        self.explanations = PredictionExplanationService(predictor, provider)
        self.risk = RiskCalculator(settings.RISK_FREE_RATE)
        self.technical_scorer = TechnicalScorer()
        self.fundamental_scorer = FundamentalScorer()
        self.valuation_scorer = ValuationScorer()
        self.sentiment_scorer = SentimentScorer()
        self.risk_scorer = RiskScorer()
        self.prediction_scorer = PredictionScorer()
        self.ai_service = explanation_service or ai_service
        self._cache: dict[
            tuple[str, str, str, str, str],
            tuple[float, RecommendationResult],
        ] = {}
        self.cache_ttl = 300

    async def get_recommendation(
        self,
        ticker: str,
        range_key: DateRangeEnum = DateRangeEnum.ONE_YEAR,
        model_type: ModelEnum = ModelEnum.RANDOM_FOREST,
        risk_tolerance: str = "balanced",
        horizon: str = "medium",
    ) -> RecommendationResult:
        symbol = ticker.strip().upper()
        cache_key = (
            symbol,
            range_key.value,
            model_type.value,
            risk_tolerance,
            horizon,
        )
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self.cache_ttl:
            return cached[1]

        stock = await self.stock_service.get_full_stock_analysis(
            symbol, range_key, model_type
        )
        fetch_range = "1y" if range_key == DateRangeEnum.ONE_MONTH else range_key.value
        history = await asyncio.to_thread(
            self.stock_service.data_provider.get_stock_data,
            symbol,
            fetch_range,
        )
        benchmark_symbol = (
            "^NSEI"
            if symbol.endswith((".NS", ".BO"))
            else "SPY"
        )
        sector_symbol = (
            None
            if symbol.endswith((".NS", ".BO"))
            else SECTOR_ETFS.get(stock.profile.sector or "")
        )

        fundamentals_task = self.fundamentals.get_metrics(symbol)
        sentiment_task = self.sentiment.analyze_ticker(symbol)
        benchmark_task = asyncio.to_thread(
            self._safe_history, benchmark_symbol, fetch_range
        )
        sector_task = asyncio.to_thread(
            self._safe_history, sector_symbol, fetch_range
        )
        explanation_task = asyncio.to_thread(
            self._safe_explanation,
            symbol,
            range_key,
            model_type,
            history,
        )
        (
            fundamentals,
            sentiment,
            benchmark,
            sector,
            explanation,
        ) = await asyncio.gather(
            fundamentals_task,
            sentiment_task,
            benchmark_task,
            sector_task,
            explanation_task,
        )

        risk_metrics = self.risk.calculate(
            history["Close"],
            history.get("Volume"),
            benchmark["Close"] if benchmark is not None else None,
            sector["Close"] if sector is not None else None,
        )
        current_price = float(
            stock.profile.current_price or history["Close"].iloc[-1]
        )
        components = {
            "technical": self.technical_scorer.calculate(history),
            "fundamental": self.fundamental_scorer.calculate(fundamentals),
            "valuation": self.valuation_scorer.calculate(fundamentals),
            "sentiment": self.sentiment_scorer.calculate(sentiment),
            "risk": self.risk_scorer.calculate(risk_metrics),
            "prediction": self.prediction_scorer.calculate(
                stock.prediction, current_price, explanation
            ),
        }
        expected_return = (
            (stock.prediction.predicted_price - current_price) / current_price
            if current_price
            else 0.0
        )
        expected_downside = self._expected_downside(
            current_price, risk_metrics, explanation
        )
        base_config = DecisionConfig.from_settings()
        config = personalize_decision_config(
            base_config, risk_tolerance, horizon
        )
        decision = DecisionEngine(config).decide(
            components,
            risk_metrics.risk_level,
            expected_return,
            expected_downside,
        )
        result = RecommendationResult(
            ticker=symbol,
            generated_at=datetime.now(timezone.utc).isoformat(),
            risk_tolerance=risk_tolerance,
            decision=decision,
            prediction_explanation=explanation,
        )
        self._cache[cache_key] = (time.time(), result)
        return result

    async def explain_recommendation(
        self, recommendation: dict[str, Any]
    ) -> str:
        """Explain an immutable decision result without letting the LLM decide."""
        decision = recommendation.get("decision") or {}
        compact = {
            "ticker": recommendation.get("ticker"),
            "risk_tolerance": recommendation.get("risk_tolerance"),
            "recommendation": decision.get("recommendation"),
            "overall_score": decision.get("overall_score"),
            "confidence": decision.get("confidence"),
            "risk_level": decision.get("risk_level"),
            "expected_return": decision.get("expected_return"),
            "expected_downside": decision.get("expected_downside"),
            "strengths": decision.get("strengths"),
            "weaknesses": decision.get("weaknesses"),
            "components": decision.get("components"),
        }
        return await self.ai_service.complete_chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Explain the supplied deterministic investment decision. "
                        "Never change the BUY/HOLD/SELL action, scores, confidence, "
                        "or risk level. Do not invent evidence. Clearly distinguish "
                        "measured inputs from uncertainty and state that this is "
                        "decision support rather than financial advice."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(compact, separators=(",", ":")),
                },
            ],
            provider="auto",
            temperature=0.1,
            max_tokens=700,
        )

    def _safe_history(
        self, ticker: str | None, range_key: str
    ) -> pd.DataFrame | None:
        if not ticker:
            return None
        try:
            return self.stock_service.data_provider.get_stock_data(
                ticker, range_key
            )
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _safe_explanation(
        self,
        ticker: str,
        range_key: DateRangeEnum,
        model_type: ModelEnum,
        history: pd.DataFrame,
    ) -> ExplanationResult | None:
        try:
            return self.explanations.explain(
                ticker, range_key, model_type, history
            )
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    @staticmethod
    def _expected_downside(
        current_price: float,
        risk: RiskMetrics,
        explanation: ExplanationResult | None,
    ) -> float:
        monthly_var = risk.value_at_risk_95 * (21.0**0.5)
        model_downside = 0.0
        if explanation is not None and current_price > 0:
            model_downside = max(
                0.0,
                (current_price - explanation.uncertainty_lower) / current_price,
            )
        return -max(monthly_var, model_downside)
