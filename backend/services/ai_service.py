import json
import logging
import httpx
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import HTTPException
from core.config import settings

logger = logging.getLogger("stock_dashboard")

class AIService:
    def __init__(self):
        # Default timeouts
        self.default_timeout = httpx.Timeout(60.0, connect=5.0)
        self.ollama_timeout = httpx.Timeout(5.0, connect=2.0)

    async def get_models(self, provider: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> List[Dict[str, str]]:   
        """Fetch available models for a provider."""
        # Normalize provider
        p = provider.lower() if provider else "groq"
        if p == "auto": p = "groq"

        logger.info(f"Fetching models for provider: {p}")
        
        if p == "ollama":
            url = f"{base_url or 'http://localhost:11434'}/api/tags"
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
        url = f"{base_url or self._get_default_base_url(p)}/models"
        headers = self._get_headers(p, api_key)

        # Special case for Gemini
        if p == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            if not key: return []
            url = f"https://generativelanguage.googleapis.com/v1/models?key={key}"
            headers = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", []) if isinstance(data, dict) else data
                    if p == "gemini":
                        return [{"id": m["name"].replace("models/", ""), "name": m["displayName"]} for m in models if "models/" in m.get("name", "")]

                    return [{"id": m.get("id", ""), "name": m.get("id", "")} for m in models if m.get("id")]
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
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions from various providers with fallback."""
        
        # Normalize provider
        p = provider.lower() if provider else "groq"
        if p == "auto": p = "groq"

        primary_config = {
            "provider": p,
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }
        
        configs = [primary_config]
        
        # Add fallbacks only if they are different from primary
        if p != "ollama":
            configs.append({"provider": "ollama", "api_key": None, "base_url": "http://localhost:11434", "model": "llama3"})
        
        if p != "groq" or (p == "groq" and api_key):
            # If primary was a user-provided groq key, fallback to app default groq key
            configs.append({"provider": "groq", "api_key": settings.DEFAULT_GROQ_API_KEY, "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"})

        # Filter out invalid configs and duplicates
        seen = set()
        valid_configs = []
        for c in configs:
            key = (c["provider"], c["api_key"], c["base_url"], c["model"])
            if key in seen: continue
            seen.add(key)
            
            if c["provider"] == "groq" and not (c["api_key"] or settings.DEFAULT_GROQ_API_KEY): continue
            if c["provider"] == "openai" and not c["api_key"] and not c["base_url"]: continue
            valid_configs.append(c)

        last_error = None
        for config in valid_configs:
            logger.info(f"Attempting stream: provider={config['provider']}, model={config['model']}")
            try:
                success = False
                async for chunk in self._attempt_stream(
                    messages=messages,
                    provider=config["provider"],
                    model=config["model"],
                    api_key=config["api_key"],
                    base_url=config["base_url"],
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
                    success = True
                
                if success:
                    logger.info(f"Stream successful with {config['provider']}")
                    yield "data: [DONE]\n\n"
                    return
            except Exception as e:
                logger.error(f"Stream attempt failed for {config['provider']}: {str(e)}")
                last_error = e
                continue

        if last_error:
            yield f"data: {json.dumps({'error': str(last_error)})}\n\n"
        yield "data: [DONE]\n\n"

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
            payload = {
                "model": model or "llama3",
                "messages": messages,
                "stream": True
            }

        # Special handling for Gemini
        if provider == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            model_id = model or "gemini-1.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:streamGenerateContent?alt=sse&key={key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"role": "user" if m["role"].lower() == "user" else "model", "parts": [{"text": m["content"]}]} for m in messages if m["role"].lower() != "system"],
                "systemInstruction": {"parts": [{"text": next((m["content"] for m in messages if m["role"].lower() == "system"), "")}]}
            }

        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider == "gemini":
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        raise Exception(f"Gemini error ({response.status_code}): {error_body.decode()}")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                if text:
                                    yield f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\n"
                            except: pass
                return

            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"{provider} error ({response.status_code}): {error_text.decode()}")

                async for line in response.aiter_lines():
                    if not line.strip(): continue

                    if provider == "ollama":
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': token}}]})}\n\n"
                            if data.get("done"):
                                break
                        except: pass
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
            "groq": "llama-3.3-70b-versatile",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20240620",
            "gemini": "gemini-1.5-flash",
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
