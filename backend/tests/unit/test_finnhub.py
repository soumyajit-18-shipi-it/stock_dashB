from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from services.finnhub_service import FinnhubService


@pytest.mark.asyncio
async def test_finnhub_service_success() -> None:
    svc = FinnhubService()
    svc.api_key = "dummy_key"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "Apple Inc."}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        profile = await svc.get_company_profile("AAPL")
        assert profile == {"name": "Apple Inc."}
        assert svc.last_latency >= 0
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_finnhub_service_no_key() -> None:
    svc = FinnhubService()
    svc.api_key = None

    profile = await svc.get_company_profile("AAPL")
    assert profile is None


@pytest.mark.asyncio
async def test_finnhub_service_error_status() -> None:
    svc = FinnhubService()
    svc.api_key = "dummy_key"

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        profile = await svc.get_company_profile("AAPL")
        assert profile is None


@pytest.mark.asyncio
async def test_finnhub_service_exception() -> None:
    svc = FinnhubService()
    svc.api_key = "dummy_key"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("network error")
        profile = await svc.get_company_profile("AAPL")
        assert profile is None
