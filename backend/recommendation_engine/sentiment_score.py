"""Finance-model news sentiment component."""

from sentiment import SentimentResult

from recommendation_engine.types import ScoreResult, bounded_score


class SentimentScorer:
    def calculate(self, sentiment: SentimentResult) -> ScoreResult:
        if sentiment.confidence <= 0:
            return ScoreResult(
                0.0,
                0.0,
                "Finance sentiment model is unavailable",
                metrics=sentiment.to_dict(),
            )
        score = bounded_score(sentiment.positive - sentiment.negative)
        evidence = tuple(
            f"{item.label.title()}: {item.headline}"
            for item in sentiment.top_reasons[:3]
        )
        label = "positive" if score > 0.1 else "negative" if score < -0.1 else "mixed"
        return ScoreResult(
            score=round(score, 6),
            confidence=round(sentiment.confidence, 6),
            reason=f"Recent finance news is {label}",
            evidence=evidence,
            metrics=sentiment.to_dict(),
        )
