import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
import httpx
from typing import List, Dict, Optional, AsyncGenerator

from core.config import settings

logger = logging.getLogger("stock_dashboard")
AI_PROVIDER_CONFIG_ERROR = "AI provider is not configured"
AI_PROVIDER_SETUP_HINT = "Set GROQ_API_KEY or DEFAULT_GROQ_API_KEY in the backend environment."


class AIProviderError(RuntimeError):
    code = "AI_PROVIDER_ERROR"
    status_code = 503

    def __init__(self, message: str, *, code: Optional[str] = None) -> None:
        super().__init__(message)
        if code:
            self.code = code


class AIProviderNotConfigured(AIProviderError):
    code = "AI_PROVIDER_NOT_CONFIGURED"
    status_code = 503

    def __init__(self) -> None:
        super().__init__(AI_PROVIDER_CONFIG_ERROR)


class AIProviderConnectionFailed(AIProviderError):
    code = "AI_PROVIDER_CONNECTION_FAILED"
    status_code = 503

    def __init__(self) -> None:
        super().__init__("Unable to connect to AI provider")


class AIProviderEmptyResponse(AIProviderError):
    code = "AI_EMPTY_RESPONSE"
    status_code = 502

    def __init__(self) -> None:
        super().__init__("AI provider returned an empty response")


class AIProviderTimeout(AIProviderError):
    code = "AI_PROVIDER_TIMEOUT"
    status_code = 504

    def __init__(self) -> None:
        super().__init__("AI provider request timed out")


@dataclass(frozen=True)
class ResolvedAIProvider:
    provider: str
    api_key: Optional[str]
    base_url: str
    model: str
    streaming_supported: bool = True
    report_generation_supported: bool = True


class AIService:
    def __init__(self) -> None:

        # Default timeouts
        timeout_seconds = max(1, int(settings.AI_REQUEST_TIMEOUT_SECONDS or 45))
        self.default_timeout = httpx.Timeout(float(timeout_seconds), connect=10.0)
        self.ollama_timeout = httpx.Timeout(5.0, connect=2.0)

    def resolve_provider(self, provider: Optional[str] = None, model: Optional[str] = None) -> ResolvedAIProvider:
        explicit = (provider or settings.AI_PROVIDER or "").strip().lower()
        if explicit == "auto":
            explicit = ""

        candidates: list[str]
        if explicit:
            candidates = [explicit]
        else:
            candidates = []
            if settings.GROQ_API_KEY or settings.DEFAULT_GROQ_API_KEY:
                candidates.append("groq")
            if settings.OPENAI_API_KEY:
                candidates.append("openai")
            if settings.OPENROUTER_API_KEY:
                candidates.append("openrouter")
            if settings.OLLAMA_BASE_URL and settings.is_development:
                candidates.append("ollama")

        for candidate in candidates:
            key = self._get_default_key(candidate)
            if candidate in {"groq", "openai", "openrouter"} and not key:
                continue
            if candidate == "ollama" and not settings.OLLAMA_BASE_URL:
                continue
            if candidate == "ollama" and not settings.is_development and not explicit:
                continue
            return ResolvedAIProvider(
                provider=candidate,
                api_key=key,
                base_url=settings.OLLAMA_BASE_URL if candidate == "ollama" else self._get_default_base_url(candidate),
                model=model or settings.AI_MODEL or self._get_default_model(candidate),
            )

        raise AIProviderNotConfigured()

    def health(self) -> dict[str, object]:
        try:
            resolved = self.resolve_provider()
        except AIProviderNotConfigured:
            return {
                "configured": False,
                "provider": None,
                "error": AI_PROVIDER_CONFIG_ERROR,
                "code": "AI_PROVIDER_NOT_CONFIGURED",
            }

        return {
            "configured": True,
            "provider": resolved.provider,
            "model": resolved.model,
            "streaming_supported": resolved.streaming_supported,
            "report_generation_supported": resolved.report_generation_supported,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def startup_diagnostics(self) -> dict[str, object]:
        health = self.health()
        return {
            "configured": health.get("configured", False),
            "provider": health.get("provider"),
            "model": health.get("model"),
        }

    async def get_models(
        self,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Fetch available models for a provider."""
        try:
            resolved = self.resolve_provider(provider)
        except AIProviderNotConfigured:
            return self._get_fallback_models("groq")

        p = resolved.provider

        logger.info(f"Fetching models for provider: {p}")

        if p == "ollama":
            url = f"{resolved.base_url}/api/tags"
            try:
                async with httpx.AsyncClient(timeout=self.ollama_timeout) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        return [{"id": m["name"], "name": m["name"]} for m in models]
            except Exception as e:
                logger.warning(f"Ollama models fetch failed: {str(e)}")
                return []

        # Default to OpenAI-compatible for most providers
        url = f"{resolved.base_url}/models"
        headers = self._get_headers(p, resolved.api_key)

        # Special case for Gemini
        if p == "gemini":
            key = settings.GEMINI_API_KEY
            if not key:
                return []
            url = f"https://generativelanguage.googleapis.com/v1/models?key={key}"
            headers = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", []) if isinstance(data, dict) else data
                    if p == "gemini":
                        return [
                            {
                                "id": m["name"].replace("models/", ""),
                                "name": m["displayName"],
                            }
                            for m in models
                            if "models/" in m.get("name", "")
                        ]

                    return [
                        {"id": m.get("id", ""), "name": m.get("id", "")}
                        for m in models
                        if m.get("id")
                    ]
        except Exception as e:
            logger.error(f"Models fetch failed for {p}: {str(e)}")

        return self._get_fallback_models(p)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        provider: str = "groq",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 8000,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions from the backend-configured provider."""

        try:
            resolved = self.resolve_provider(provider, model)
            logger.info(
                "Attempting AI stream: provider=%s, model=%s",
                resolved.provider,
                resolved.model,
            )
            token_count = 0
            async for chunk in self._attempt_stream(
                messages=messages,
                provider=resolved.provider,
                model=resolved.model,
                api_key=resolved.api_key,
                base_url=resolved.base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                token_count += 1
                yield chunk

            if token_count == 0:
                raise AIProviderEmptyResponse()

            logger.info("AI stream successful with provider=%s", resolved.provider)
            yield "data: [DONE]\n\n"
        except AIProviderError as exc:
            logger.warning("AI stream failed: %s: %s", exc.__class__.__name__, str(exc))
            yield f"data: {json.dumps({'error': str(exc), 'code': exc.code})}\n\n"
            yield "data: [DONE]\n\n"
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning("AI provider connection failed: %s", exc.__class__.__name__)
            error = AIProviderConnectionFailed()
            yield f"data: {json.dumps({'error': str(error), 'code': error.code})}\n\n"
            yield "data: [DONE]\n\n"
        except httpx.TimeoutException as exc:
            logger.warning("AI provider timed out: %s", exc.__class__.__name__)
            error = AIProviderTimeout()
            yield f"data: {json.dumps({'error': str(error), 'code': error.code})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.warning("AI provider failed: %s: %s", exc.__class__.__name__, str(exc))
            error = AIProviderConnectionFailed()
            yield f"data: {json.dumps({'error': str(error), 'code': error.code})}\n\n"
            yield "data: [DONE]\n\n"

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        provider: str = "auto",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 8000,
    ) -> str:
        full_content = ""
        stream_error: Optional[AIProviderError] = None
        async for chunk in self.stream_chat(
            messages=messages,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            if not chunk.startswith("data: "):
                continue
            data_str = chunk[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
            except Exception:
                continue
            if "error" in data:
                stream_error = AIProviderError(
                    str(data.get("error") or "AI provider error"),
                    code=str(data.get("code") or "AI_PROVIDER_ERROR"),
                )
                break
            full_content += data.get("choices", [{}])[0].get("delta", {}).get("content", "")

        if stream_error:
            if stream_error.code == AIProviderNotConfigured.code:
                raise AIProviderNotConfigured()
            if stream_error.code == AIProviderEmptyResponse.code:
                raise AIProviderEmptyResponse()
            if stream_error.code == AIProviderTimeout.code:
                raise AIProviderTimeout()
            raise AIProviderConnectionFailed()

        if not full_content.strip():
            raise AIProviderEmptyResponse()

        return full_content

    async def _attempt_stream(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        model: Optional[str],
        api_key: Optional[str],
        base_url: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        url = f"{base_url or self._get_default_base_url(provider)}/chat/completions"
        headers = self._get_headers(provider, api_key)

        payload = {
            "model": model or self._get_default_model(provider),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # Special handling for Ollama
        timeout = self.default_timeout
        if provider == "ollama":
            timeout = self.ollama_timeout
            url = f"{base_url or 'http://localhost:11434'}/api/chat"
            payload = {"model": model or "llama3", "messages": messages, "stream": True}

        # Special handling for Gemini
        if provider == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            model_id = model or "gemini-1.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:streamGenerateContent?alt=sse&key={key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "role": "user" if m["role"].lower() == "user" else "model",
                        "parts": [{"text": m["content"]}],
                    }
                    for m in messages
                    if m["role"].lower() != "system"
                ],
                "systemInstruction": {
                    "parts": [
                        {
                            "text": next(
                                (
                                    m["content"]
                                    for m in messages
                                    if m["role"].lower() == "system"
                                ),
                                "",
                            )
                        }
                    ]
                },
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                },
            }

        try:
            client_context = httpx.AsyncClient(timeout=timeout)
        except TypeError:
            client_context = httpx.AsyncClient()

        async with client_context as client:
            if provider == "gemini":
                async with client.stream(
                    "POST", url, headers=headers, json=payload
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        raise Exception(
                            f"Gemini error ({response.status_code}): {error_body.decode()}"
                        )
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                text = (
                                    data.get("candidates", [{}])[0]
                                    .get("content", {})
                                    .get("parts", [{}])[0]
                                    .get("text", "")
                                )
                                if text:
                                    yield f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\n"
                            except Exception:
                                pass
                return

            async with client.stream(
                "POST", url, headers=headers, json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.warning(
                        "AI provider returned non-200 response: provider=%s status=%s",
                        provider,
                        response.status_code,
                    )
                    raise Exception(
                        f"{provider} error ({response.status_code}): {error_text.decode()}"
                    )

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    if provider == "ollama":
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': token}}]})}\n\n"
                            if data.get("done"):
                                break
                        except Exception:
                            pass
                    else:
                        if line.startswith("{"):
                            yield f"data: {line}\n\n"
                        else:
                            yield f"{line}\n\n"

    def _get_default_base_url(self, provider: str) -> str:
        defaults = {
            "groq": "https://api.groq.com/openai/v1",
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1",
        }
        return defaults.get(provider, "")

    def _get_headers(self, provider: str, api_key: Optional[str]) -> Dict[str, str]:
        key = api_key or self._get_default_key(provider)
        headers = {"Content-Type": "application/json"}
        if key:
            if provider == "anthropic":
                headers["x-api-key"] = key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {key}"
        return headers

    def _get_default_key(self, provider: str) -> Optional[str]:
        keys = {
            "groq": settings.DEFAULT_GROQ_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "openrouter": settings.OPENROUTER_API_KEY,
        }
        return keys.get(provider)

    def _get_default_model(self, provider: str) -> str:
        models = {
            "groq": "llama-3.1-8b-instant",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20240620",
            "gemini": "gemini-1.5-flash",
            "openrouter": "openai/gpt-4o-mini",
        }
        return models.get(provider, "gpt-3.5-turbo")

    def _get_fallback_models(self, provider: str) -> List[Dict[str, str]]:
        if provider == "groq":
            return [
                {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile"},
                {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
            ]
        return []


ai_service = AIService()
