# Services Deep Dive

## Backend Services (`backend/services/`)

### `stock_service.py`
- **Role:** The primary orchestrator.
- **Logic:** Calls `StockDataProvider` for data, `FeatureEngineer` for indicators, and `StockPredictor` for ML.
- **Caching:** Implements logic to check if a ticker's data is fresh in the cache before making external requests.

### `ai_service.py`
- **Role:** LLM Interface.
- **Capabilities:** Supports Groq, OpenAI, Gemini, and Anthropic.
- **Feature:** Streaming responses via Python generators for a "typing" effect in the UI.

### `watchlist_service.py` & `history_service.py`
- **Role:** CRUD wrappers for Supabase interactions.
- **Functionality:** Handles the mapping between API models and database rows.

## Frontend Services (`frontend/src/services/`)

### `api_client.ts`
- **Role:** Centralized `fetch` wrapper.
- **Responsibility:** Handles HTTP requests to the FastAPI backend and provides local-first fallback using `localStorage`.

### `aiProviderService.ts`
- **Role:** Client-side LLM orchestration.
- **Logic:** Manages API keys, model selection, and streaming event listeners for the `AskAIDrawer`.
