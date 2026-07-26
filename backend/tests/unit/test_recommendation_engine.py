from recommendation_engine.config import DecisionConfig
from recommendation_engine.decision_engine import DecisionEngine
from recommendation_engine.types import ScoreResult


def _component(score: float, confidence: float = 0.9) -> ScoreResult:
    return ScoreResult(
        score=score,
        confidence=confidence,
        reason="evidence",
        evidence=("evidence",),
    )


def test_prediction_alone_cannot_trigger_buy() -> None:
    components = {
        "technical": _component(0.0),
        "fundamental": _component(0.0),
        "valuation": _component(0.0),
        "sentiment": _component(0.0),
        "risk": _component(0.0),
        "prediction": _component(1.0),
    }

    result = DecisionEngine(DecisionConfig()).decide(
        components, "medium", 0.10, -0.05
    )

    assert result.recommendation == "HOLD"
    assert result.policy_checks["diverse_buy_evidence"] is False


def test_diverse_high_confidence_evidence_can_trigger_buy() -> None:
    components = {
        "technical": _component(0.75),
        "fundamental": _component(0.80),
        "valuation": _component(0.55),
        "sentiment": _component(0.35),
        "risk": _component(0.40),
        "prediction": _component(0.60),
    }

    result = DecisionEngine(DecisionConfig()).decide(
        components, "low", 0.08, -0.04
    )

    assert result.recommendation == "BUY"
    assert result.overall_score >= 65
    assert result.confidence >= 0.45


def test_low_coverage_forces_hold() -> None:
    components = {
        name: _component(0.9, 0.0)
        for name in (
            "technical",
            "fundamental",
            "valuation",
            "sentiment",
            "risk",
            "prediction",
        )
    }
    result = DecisionEngine(DecisionConfig()).decide(
        components, "unknown", 0.0, 0.0
    )
    assert result.recommendation == "HOLD"
    assert result.policy_checks["minimum_coverage"] is False
