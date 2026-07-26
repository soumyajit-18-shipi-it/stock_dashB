"""Financial-news sentiment via a configurable Hugging Face model.

No generic-language or keyword heuristic is substituted when inference is
unavailable. The service returns a neutral result with zero confidence so the
decision engine can exclude that component instead of presenting fabricated
certainty.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from core.config import settings
from services.finnhub_service import FinnhubService, finnhub_service

logger = logging.getLogger("stock_dashboard")


@dataclass(frozen=True)
class HeadlineSentiment:
    headline: str
    source: str | None
    url: str | None
    published_at: int | None
    label: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SentimentResult:
    positive: float
    negative: float
    neutral: float
    confidence: float
    model: str
    provider_status: str
    top_reasons: tuple[HeadlineSentiment, ...]
    article_count: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["top_reasons"] = [item.to_dict() for item in self.top_reasons]
        return data


class SentimentService:
    ROUTER_URL = "https://router.huggingface.co/hf-inference/models"

    def __init__(
        self,
        finnhub: FinnhubService | None = None,
        model_id: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self.finnhub = finnhub or finnhub_service
        self.model_id = model_id or settings.FINANCIAL_SENTIMENT_MODEL
        self.api_token = (
            settings.HUGGINGFACE_API_TOKEN if api_token is None else api_token
        )
        self._cache: dict[str, tuple[float, SentimentResult]] = {}
        self.cache_ttl = 15 * 60
        self.max_articles = 20

    async def analyze_ticker(self, ticker: str) -> SentimentResult:
        news = await self.finnhub.get_company_news(ticker)
        return await self.analyze_articles(news)

    async def analyze_articles(
        self, articles: list[dict[str, Any]]
    ) -> SentimentResult:
        selected = [
            item
            for item in articles
            if str(item.get("headline") or "").strip()
        ][: self.max_articles]
        if not selected:
            return self._unavailable("no_news")

        headlines = [str(item["headline"]).strip() for item in selected]
        cache_key = hashlib.sha256(
            (self.model_id + "\n" + "\n".join(headlines)).encode("utf-8")
        ).hexdigest()
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self.cache_ttl:
            return cached[1]
        if not self.api_token:
            return self._unavailable("missing_huggingface_token", len(selected))

        try:
            response_payload = await self._infer(headlines)
            distributions = self._normalize_response(
                response_payload, expected=len(headlines)
            )
            result = self._aggregate(selected, distributions)
            self._cache[cache_key] = (time.time(), result)
            return result
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Financial sentiment inference failed: %s", exc)
            return self._unavailable("inference_unavailable", len(selected))

    async def _infer(self, headlines: list[str]) -> Any:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.SENTIMENT_REQUEST_TIMEOUT_SECONDS, connect=5.0
            )
        ) as client:
            response = await client.post(
                f"{self.ROUTER_URL}/{self.model_id}",
                headers=headers,
                json={
                    "inputs": headlines,
                    "parameters": {"top_k": 3},
                    "options": {"wait_for_model": False},
                },
            )
            response.raise_for_status()
            return response.json()

    def _normalize_response(
        self, payload: Any, expected: int
    ) -> list[dict[str, float]]:
        if not isinstance(payload, list):
            raise ValueError("Unexpected sentiment response")
        rows = payload
        if expected == 1 and rows and isinstance(rows[0], dict):
            rows = [rows]
        if len(rows) != expected:
            raise ValueError("Sentiment response count mismatch")
        normalized: list[dict[str, float]] = []
        label_aliases = {
            "label_0": "negative",
            "label_1": "neutral",
            "label_2": "positive",
        }
        for row in rows:
            if not isinstance(row, list):
                raise ValueError("Unexpected sentiment label row")
            distribution = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
            for item in row:
                if not isinstance(item, dict):
                    continue
                raw_label = str(item.get("label") or "").lower()
                label = label_aliases.get(raw_label, raw_label)
                if label in distribution:
                    distribution[label] = float(item.get("score") or 0.0)
            total = sum(distribution.values())
            if total <= 0:
                raise ValueError("Sentiment response contained no known labels")
            normalized.append(
                {key: value / total for key, value in distribution.items()}
            )
        return normalized

    def _aggregate(
        self,
        articles: list[dict[str, Any]],
        distributions: list[dict[str, float]],
    ) -> SentimentResult:
        count = len(distributions)
        positive = sum(row["positive"] for row in distributions) / count
        negative = sum(row["negative"] for row in distributions) / count
        neutral = sum(row["neutral"] for row in distributions) / count
        per_article: list[HeadlineSentiment] = []
        for article, distribution in zip(articles, distributions):
            label = max(distribution, key=distribution.get)  # type: ignore[arg-type]
            per_article.append(
                HeadlineSentiment(
                    headline=str(article["headline"]),
                    source=str(article.get("source") or "") or None,
                    url=str(article.get("url") or "") or None,
                    published_at=self._integer(article.get("datetime")),
                    label=label,
                    score=round(distribution[label], 6),
                )
            )
        top_reasons = tuple(
            sorted(
                per_article,
                key=lambda item: (
                    item.label != "neutral",
                    item.score,
                    item.published_at or 0,
                ),
                reverse=True,
            )[:5]
        )
        confidence = (positive + negative) * (
            sum(max(row.values()) for row in distributions) / count
        )
        return SentimentResult(
            positive=round(positive, 6),
            negative=round(negative, 6),
            neutral=round(neutral, 6),
            confidence=round(confidence, 6),
            model=self.model_id,
            provider_status="available",
            top_reasons=top_reasons,
            article_count=count,
        )

    def _unavailable(
        self, status: str, article_count: int = 0
    ) -> SentimentResult:
        return SentimentResult(
            positive=0.0,
            negative=0.0,
            neutral=1.0,
            confidence=0.0,
            model=self.model_id,
            provider_status=status,
            top_reasons=(),
            article_count=article_count,
        )

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
