import pytest

from sentiment.service import SentimentService


@pytest.mark.asyncio
async def test_sentiment_without_token_is_excluded_not_guessed() -> None:
    service = SentimentService(api_token="")
    result = await service.analyze_articles(
        [{"headline": "Revenue increased substantially", "source": "test"}]
    )
    assert result.provider_status == "missing_huggingface_token"
    assert result.confidence == 0
    assert result.neutral == 1


@pytest.mark.asyncio
async def test_sentiment_aggregates_three_way_probabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = SentimentService(api_token="test-token")

    async def fake_infer(_: list[str]) -> list[list[dict[str, float | str]]]:
        return [
            [
                {"label": "positive", "score": 0.8},
                {"label": "neutral", "score": 0.15},
                {"label": "negative", "score": 0.05},
            ],
            [
                {"label": "positive", "score": 0.1},
                {"label": "neutral", "score": 0.2},
                {"label": "negative", "score": 0.7},
            ],
        ]

    monkeypatch.setattr(service, "_infer", fake_infer)
    result = await service.analyze_articles(
        [
            {"headline": "Earnings beat estimates", "source": "A"},
            {"headline": "Guidance was cut", "source": "B"},
        ]
    )
    assert result.provider_status == "available"
    assert result.article_count == 2
    assert result.positive == pytest.approx(0.45)
    assert result.negative == pytest.approx(0.375)
    assert len(result.top_reasons) == 2
