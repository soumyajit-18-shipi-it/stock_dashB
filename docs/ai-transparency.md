# AI Transparency

## AI Features

- Ask AI drawer for stock questions.
- AI watchlist suggestions.
- AI report PDF generation.
- Optional Indic intent routing hint before AI chat.

## Providers

| Provider | Default / Example Model | Environment Variable | Data Sent | Notes |
| --- | --- | --- | --- | --- |
| Groq | `llama-3.3-70b-versatile` | `DEFAULT_GROQ_API_KEY` | Prompt, stock context, recent candles | Hosted external API |
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` | Prompt and stock context | Hosted external API |
| Anthropic | `claude-3-5-sonnet-20240620` | `ANTHROPIC_API_KEY` | Prompt and stock context | Hosted external API |
| Gemini | `gemini-1.5-flash` | `GEMINI_API_KEY` | Prompt and stock context | Hosted external API |
| OpenRouter | User-selected | `OPENROUTER_API_KEY` | Prompt and stock context | External routing provider |
| Ollama | `llama3` default | None | Prompt and stock context to local server | Local runtime if user runs Ollama |

## Fallback Behavior

`backend/services/ai_service.py` tries the selected provider, then local Ollama when applicable, then Groq if a default app key is configured. Failures are surfaced as errors in the UI.

## Privacy

Hosted providers receive the user prompt and stock context. API keys entered in the UI are stored in browser `localStorage` and passed per request; they are not stored in Supabase by the application code.

## Financial Safety

AI output is for education and analysis support. It is not a registered investment adviser and must not be treated as financial advice.
