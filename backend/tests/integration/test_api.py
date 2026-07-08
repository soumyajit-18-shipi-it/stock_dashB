import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add project root and backend to sys.path
root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.supabase_client import MockTableQuery  # noqa: E402
from core.config import settings  # noqa: E402


class TestAPIEndpoints:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ai_health_check_safe_response(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/ai")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "api_key" not in data
        assert "secret" not in data

    def test_supabase_health_check(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/supabase")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "using_mock_client" in data

    def test_ai_chat_missing_provider_returns_json_error(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "AI_PROVIDER", "")
        monkeypatch.setattr(settings, "GROQ_API_KEY", "")
        monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "")
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
        monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
        monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "")

        response = client.post(
            "/api/v1/ai/chat",
            json={"messages": [{"role": "user", "content": "hello"}], "stream": False},
        )
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["code"] == "AI_PROVIDER_NOT_CONFIGURED"
        assert detail["error"] == "AI provider is not configured"

    def test_root_endpoint(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.integration
    def test_stock_endpoint_invalid_ticker(self, client: TestClient) -> None:
        response = client.get("/api/v1/stock/INVALID_TICKER_XYZ123")
        assert response.status_code in [404, 500]

    def test_watchlist_get_empty(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/watchlist",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_history_get_empty(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/history",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_predictions_get(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/predictions",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    def test_watchlist_rows_are_scoped_by_user_id(self, client: TestClient) -> None:
        user_a_headers = {"Authorization": "Bearer valid-token"}
        user_b_headers = {"Authorization": "Bearer mock-user-b-token"}

        response = client.post(
            "/api/v1/watchlist",
            headers=user_a_headers,
            json={"ticker": "AAPL", "name": "Apple Inc."},
        )
        assert response.status_code == 200
        assert response.json()["ticker"] == "AAPL"

        response = client.get("/api/v1/watchlist", headers=user_a_headers)
        assert response.status_code == 200
        assert [item["ticker"] for item in response.json()] == ["AAPL"]

        response = client.get("/api/v1/watchlist", headers=user_b_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_search_history_rows_are_scoped_by_user_id(self, client: TestClient) -> None:
        user_a_headers = {"Authorization": "Bearer valid-token"}
        user_b_headers = {"Authorization": "Bearer mock-user-b-token"}

        response = client.post(
            "/api/v1/history",
            headers=user_a_headers,
            json={"query": "AAPL", "ticker": "AAPL"},
        )
        assert response.status_code == 200
        assert response.json()["ticker"] == "AAPL"

        response = client.get("/api/v1/history", headers=user_a_headers)
        assert response.status_code == 200
        assert [item["ticker"] for item in response.json()] == ["AAPL"]

        response = client.get("/api/v1/history", headers=user_b_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_feedback_submission_requires_auth(self, client: TestClient) -> None:
        response = client.post("/api/v1/feedback", json={
            "category": "bug_report",
            "title": "Test Bug",
            "description": "This is a test bug report"
        })
        assert response.status_code == 401

    def test_feedback_category_validation(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "category": "invalid_category_xyz",
                "title": "Test Bug",
                "description": "This is a test bug report"
            }
        )
        assert response.status_code == 400

        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "category": "bug_report",
                "title": "Test Bug",
                "description": "This is a test bug report"
            }
        )
        assert response.status_code == 200
        assert response.json()["category"] == "bug_report"

    def test_my_feedback_returns_only_own_issues(self, client: TestClient) -> None:
        client.post(
            "/api/v1/feedback",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "category": "bug_report",
                "title": "User issue",
                "description": "Description"
            }
        )
        client.post(
            "/api/v1/feedback",
            headers={"Authorization": "Bearer admin-token"},
            json={
                "category": "feature_request",
                "title": "Admin issue",
                "description": "Description"
            }
        )

        response = client.get(
            "/api/v1/feedback/my",
            headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for item in data:
            assert item["user_id"] == "mock-user-id"

    def test_admin_stats_blocks_unauthenticated(self, client: TestClient) -> None:
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401

    def test_admin_stats_blocks_non_admin(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 403

    def test_admin_stats_allows_configured_admin(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer admin-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_feedback_issues" in data
        assert "open_feedback_issues" in data
        assert "latest_signups" in data
        assert "recent_feedback" in data
        assert "users" in data

    def test_admin_stats_includes_user_analytics_and_submitter_name(self, client: TestClient) -> None:
        MockTableQuery._store["user_profiles"] = [
            {
                "id": "mock-user-id",
                "email": "regular_user@example.com",
                "full_name": "Regular User",
                "avatar_url": "https://example.com/avatar.png",
                "provider": "google",
                "first_seen_at": "2026-06-26T00:00:00+00:00",
                "last_seen_at": "2026-06-26T01:00:00+00:00",
                "created_at": "2026-06-26T00:00:00+00:00",
                "updated_at": "2026-06-26T01:00:00+00:00",
            }
        ]
        MockTableQuery._store["feedback_issues"] = [
            {
                "id": "feedback-1",
                "user_id": "mock-user-id",
                "email": "regular_user@example.com",
                "category": "bug_report",
                "title": "Broken chart",
                "description": "The chart is blank",
                "status": "open",
                "priority": "normal",
                "created_at": "2026-06-26T02:00:00+00:00",
                "updated_at": "2026-06-26T02:00:00+00:00",
            }
        ]
        MockTableQuery._store["watchlists"] = [
            {"id": "watch-1", "user_id": "mock-user-id", "ticker": "AAPL"}
        ]
        MockTableQuery._store["search_history"] = [
            {"id": "search-1", "user_id": "mock-user-id", "ticker": "AAPL"}
        ]

        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 1
        assert data["latest_signups"][0]["full_name"] == "Regular User"
        assert data["users"][0]["total_feedback_count"] == 1
        assert data["users"][0]["total_watchlist_items"] == 1
        assert data["users"][0]["total_searches"] == 1
        assert data["recent_feedback"][0]["submitter_name"] == "Regular User"
        assert data["recent_feedback"][0]["submitter_avatar_url"] == "https://example.com/avatar.png"

    def test_admin_feedback_resolves_submitter_by_email_without_user_id(self, client: TestClient) -> None:
        MockTableQuery._store["user_profiles"] = [
            {
                "id": "profile-1",
                "email": "email.only@example.com",
                "full_name": "Email Only User",
                "provider": "google",
                "first_seen_at": "2026-06-26T00:00:00+00:00",
                "last_seen_at": "2026-06-26T00:00:00+00:00",
                "created_at": "2026-06-26T00:00:00+00:00",
                "updated_at": "2026-06-26T00:00:00+00:00",
            }
        ]
        MockTableQuery._store["feedback_issues"] = [
            {
                "id": "feedback-email-only",
                "user_id": None,
                "email": "email.only@example.com",
                "category": "feature_request",
                "title": "Add export",
                "description": "Please add export",
                "status": "open",
                "priority": "normal",
                "created_at": "2026-06-26T02:00:00+00:00",
                "updated_at": "2026-06-26T02:00:00+00:00",
            }
        ]

        response = client.get(
            "/api/v1/admin/feedback",
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["submitter_name"] == "Email Only User"
        assert data[0]["email"] == "email.only@example.com"

    def test_user_count_endpoint_does_not_expose_emails(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/admin/user-count",
            headers={"Authorization": "Bearer admin-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "emails" not in data
        assert "email" not in data
        assert "user_profiles" not in data

