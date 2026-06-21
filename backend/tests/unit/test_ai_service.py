from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from services.ai_service import AIService


def test_ai_service_helpers() -> None:
    svc = AIService()

    # Test _get_default_base_url
    assert svc._get_default_base_url("groq") == "https://api.groq.com/openai/v1"
    assert svc._get_default_base_url("openai") == "https://api.openai.com/v1"
    assert svc._get_default_base_url("unknown") == ""

    # Test _get_default_model
    assert svc._get_default_model("groq") == "llama-3.3-70b-versatile"
    assert svc._get_default_model("openai") == "gpt-4o-mini"
    assert svc._get_default_model("unknown") == "gpt-3.5-turbo"

    # Test _get_fallback_models
    assert len(svc._get_fallback_models("groq")) == 3
    assert not svc._get_fallback_models("openai")

    # Test _get_headers
    headers_anthropic = svc._get_headers("anthropic", "test-key")
    assert headers_anthropic["x-api-key"] == "test-key"
    assert headers_anthropic["anthropic-version"] == "2023-06-01"

    headers_openai = svc._get_headers("openai", "test-key")
    assert headers_openai["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_ai_service_get_models_ollama() -> None:
    svc = AIService()

    # Mock httpx.AsyncClient.get for Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "llama3:latest"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        models = await svc.get_models("ollama", base_url="http://localhost:11434")
        assert len(models) == 1
        assert models[0]["id"] == "llama3:latest"


@pytest.mark.asyncio
async def test_ai_service_get_models_openai() -> None:
    svc = AIService()

    # Mock httpx.AsyncClient.get for OpenAI-like
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        models = await svc.get_models("openai", api_key="test-key")
        assert len(models) == 1
        assert models[0]["id"] == "gpt-4"
