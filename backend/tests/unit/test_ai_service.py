from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from core.config import settings
from services.ai_service import (
    AIProviderConnectionFailed,
    AIProviderEmptyResponse,
    AIProviderNotConfigured,
    AIProviderTimeout,
    AIService,
)


def test_ai_service_helpers() -> None:
    svc = AIService()

    # Test _get_default_base_url
    assert svc._get_default_base_url("groq") == "https://api.groq.com/openai/v1"
    assert svc._get_default_base_url("openai") == "https://api.openai.com/v1"
    assert svc._get_default_base_url("unknown") == ""

    # Test _get_default_model
    assert svc._get_default_model("groq") == "llama-3.1-8b-instant"
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
async def test_ai_service_get_models_ollama(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    # Mock httpx.AsyncClient.get for Ollama
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "llama3:latest"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        models = await svc.get_models("ollama")
        assert len(models) == 1
        assert models[0]["id"] == "llama3:latest"


@pytest.mark.asyncio
async def test_ai_service_get_models_openai(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "configured")

    # Mock httpx.AsyncClient.get for OpenAI-like
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        models = await svc.get_models("openai")
        assert len(models) == 1
        assert models[0]["id"] == "gpt-4"


@pytest.mark.asyncio
async def test_ai_service_missing_provider_returns_clear_error(monkeypatch) -> None:
    svc = AIService()

    monkeypatch.setattr(settings, "AI_PROVIDER", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "")

    chunks = [
        chunk
        async for chunk in svc.stream_chat(
            messages=[{"role": "user", "content": "Explain Reliance stock"}],
            provider="auto",
        )
    ]

    joined = "".join(chunks)
    assert "AI provider is not configured" in joined
    assert "AI_PROVIDER_NOT_CONFIGURED" in joined

    with pytest.raises(AIProviderNotConfigured):
        await svc.complete_chat(
            messages=[{"role": "user", "content": "Explain Reliance stock"}],
            provider="auto",
        )


@pytest.mark.asyncio
async def test_ai_service_successful_response(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "configured")
    monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "configured")

    async def success_attempt(**_kwargs):
        yield 'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        yield 'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'

    monkeypatch.setattr(svc, "_attempt_stream", success_attempt)
    result = await svc.complete_chat(
        messages=[{"role": "user", "content": "hello"}],
        provider="auto",
    )
    assert result == "Hello world"


@pytest.mark.asyncio
async def test_ai_service_empty_provider_response(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "configured")
    monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "configured")

    async def empty_attempt(**_kwargs):
        if False:
            yield ""  # pragma: no cover

    monkeypatch.setattr(svc, "_attempt_stream", empty_attempt)
    with pytest.raises(AIProviderEmptyResponse):
        await svc.complete_chat(
            messages=[{"role": "user", "content": "hello"}],
            provider="auto",
        )


@pytest.mark.asyncio
async def test_ai_service_connection_failure(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "configured")
    monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "configured")

    async def fail_attempt(**_kwargs):
        raise httpx.ConnectError("connection failed")
        yield ""  # pragma: no cover

    monkeypatch.setattr(svc, "_attempt_stream", fail_attempt)
    with pytest.raises(AIProviderConnectionFailed):
        await svc.complete_chat(
            messages=[{"role": "user", "content": "hello"}],
            provider="auto",
        )


@pytest.mark.asyncio
async def test_ai_service_timeout(monkeypatch) -> None:
    svc = AIService()
    monkeypatch.setattr(settings, "GROQ_API_KEY", "configured")
    monkeypatch.setattr(settings, "DEFAULT_GROQ_API_KEY", "configured")

    async def timeout_attempt(**_kwargs):
        raise httpx.TimeoutException("timeout")
        yield ""  # pragma: no cover

    monkeypatch.setattr(svc, "_attempt_stream", timeout_attempt)
    with pytest.raises(AIProviderTimeout):
        await svc.complete_chat(
            messages=[{"role": "user", "content": "hello"}],
            provider="auto",
        )
