from typing import Any

from fastapi.testclient import TestClient

from api.investment_routes import get_recommendation_service
from main import app


class _FakeRecommendation:
    def to_dict(self) -> dict[str, Any]:
        component = {
            "score": 0.4,
            "confidence": 0.8,
            "reason": "Measured evidence",
            "evidence": ["Measured evidence"],
            "metrics": {},
            "weight": 1 / 6,
            "contribution": 0.05,
        }
        return {
            "ticker": "AAPL",
            "generated_at": "2026-07-26T00:00:00+00:00",
            "risk_tolerance": "balanced",
            "decision": {
                "recommendation": "HOLD",
                "overall_score": 60.0,
                "confidence": 0.75,
                "strengths": ["Measured evidence"],
                "weaknesses": [],
                "risk_level": "medium",
                "expected_return": 0.03,
                "expected_downside": -0.05,
                "investment_horizon": "3-12 months",
                "components": {
                    name: component
                    for name in (
                        "technical",
                        "fundamental",
                        "valuation",
                        "sentiment",
                        "risk",
                        "prediction",
                    )
                },
                "policy_checks": {
                    "minimum_confidence": True,
                    "minimum_coverage": True,
                    "diverse_buy_evidence": False,
                    "buy_risk_guard": True,
                },
            },
            "prediction_explanation": None,
        }


class _FakeRecommendationService:
    async def get_recommendation(self, *_: Any, **__: Any) -> _FakeRecommendation:
        return _FakeRecommendation()


def test_recommendation_route_contract(client: TestClient) -> None:
    app.dependency_overrides[get_recommendation_service] = (
        lambda: _FakeRecommendationService()
    )
    try:
        response = client.get(
            "/api/v1/recommendation/AAPL"
            "?range=1y&model=rf&risk_tolerance=balanced&horizon=medium"
        )
    finally:
        app.dependency_overrides.pop(get_recommendation_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["recommendation"] == "HOLD"
    assert set(payload["decision"]["components"]) == {
        "technical",
        "fundamental",
        "valuation",
        "sentiment",
        "risk",
        "prediction",
    }


def test_portfolio_csv_route_contract(client: TestClient) -> None:
    response = client.post(
        "/api/v1/portfolio/parse-csv",
        json={
            "content": (
                "ticker,quantity,average_cost\n"
                "AAPL,10,150\n"
                "MSFT,5,300\n"
            )
        },
    )
    assert response.status_code == 200
    assert [item["ticker"] for item in response.json()["holdings"]] == [
        "AAPL",
        "MSFT",
    ]


def test_portfolio_csv_route_rejects_invalid_input(client: TestClient) -> None:
    response = client.post(
        "/api/v1/portfolio/parse-csv",
        json={"content": "name,value\nAAPL,10\n"},
    )
    assert response.status_code == 400
    assert "ticker or symbol" in response.json()["detail"]


def test_openapi_exposes_new_versioned_routes(client: TestClient) -> None:
    paths = client.get("/api/v1/openapi.json").json()["paths"]
    assert "/api/v1/recommendation/{ticker}" in paths
    assert "/api/v1/prediction/explanation" in paths
    assert "/api/v1/portfolio/analyze" in paths
