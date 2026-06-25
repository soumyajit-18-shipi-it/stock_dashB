# Privacy Policy

## Data Collected

The app may process:

- Ticker searches.
- Watchlist entries.
- Prediction records.
- AI chat prompts and generated report prompts.
- Browser preferences such as theme, language, low-data mode, and AI provider settings.

## Data Not Collected by Default

- Brokerage credentials.
- Bank account details.
- Personal portfolio holdings unless a user types them into chat.
- Government IDs or contact details.

## Storage

- Watchlists, search history, and predictions may be stored in Supabase.
- AI provider settings are stored in browser `localStorage`.
- Chat history is stored locally in the browser when implemented by UI state.
- Stock model files are stored under `models/`.

## Third Parties

- Yahoo Finance/yfinance for market data.
- Finnhub for company profile metadata.
- Supabase for database storage.
- Optional LLM providers: Groq, OpenAI, Anthropic, Gemini, OpenRouter, or local Ollama.

Hosted LLM providers may receive prompts, stock context, and recent candles. Use Ollama/local mode if prompts must stay on the user's machine.

## Consent and User Data

The current Indic dataset is project-authored and contains no user data. Future user-contributed data must follow `docs/data-consent.md`.

## Retention and Deletion

See `docs/data-retention.md`. Users and maintainers should provide deletion paths for stored watchlists, search history, predictions, and contributed dataset rows.

## Security Note

The migration `supabase/migrations/20260610052130_002_allow_anon_access.sql` enables broad anonymous access for demo use. This is not appropriate for production with real user data. Production deployments should replace it with authenticated, user-scoped RLS policies.
