# AI Transparency

## AI Features

- Ask AI drawer for stock questions.
- AI watchlist suggestions.
- AI report PDF generation.
- Optional Indic intent routing hint before AI chat.

## Providers

| Provider | Default / Example Model | Environment Variable | Data Sent | Notes |
| --- | --- | --- | --- | --- |
| Groq | `llama-3.1-8b-instant` | `GROQ_API_KEY` or `DEFAULT_GROQ_API_KEY` | Prompt, stock context, recent candles | Hosted external API |
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` | Prompt and stock context | Hosted external API |
| OpenRouter | `openai/gpt-4o-mini` | `OPENROUTER_API_KEY` | Prompt and stock context | External routing provider |
| Ollama | `llama3` default | `OLLAMA_BASE_URL` | Prompt and stock context to local server | Local development only when explicitly configured on backend |

## Fallback Behavior

`backend/services/ai_service.py` resolves providers from backend environment variables only. Resolution order is explicit `AI_PROVIDER`, Groq, OpenAI, OpenRouter, then Ollama for local development when explicitly configured. Production does not fall back to local Ollama.

## Privacy

Hosted providers receive the user prompt and stock context. AI provider API keys are backend-only secrets and must be configured in Render or the local backend environment. The frontend never stores or sends provider API keys.

## Financial Safety

AI output is for education and analysis support. It is not personalized financial advice. For questions such as "should I invest in this stock?", the assistant should discuss educational context, risks, uncertainty, and the value of consulting a qualified financial adviser.
