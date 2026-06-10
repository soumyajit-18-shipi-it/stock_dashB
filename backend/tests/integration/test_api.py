import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from backend.main import app


client = TestClient(app)


class TestAPIEndpoints:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.integration
    def test_stock_endpoint_invalid_ticker(self):
        response = client.get("/api/v1/stock/INVALID_TICKER_XYZ123")
        assert response.status_code in [404, 500]

    def test_watchlist_get_empty(self):
        response = client.get("/api/v1/watchlist")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_history_get_empty(self):
        response = client.get("/api/v1/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_predictions_get(self):
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
