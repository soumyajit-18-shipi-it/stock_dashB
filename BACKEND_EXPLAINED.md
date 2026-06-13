# Backend Architecture: Deep Dive

## Structure
The backend is organized into functional modules:

### `api/`
Defines the REST interface.
- `routes.py`: Contains all endpoints (`/stock`, `/watchlist`, `/ai/chat`).

### `services/`
The business logic layer.
- `stock_service.py`: Orchestrates data fetching and ML.
- `ai_service.py`: Interfaces with LLM providers (Groq, OpenAI).
- `watchlist_service.py`: Manages user watchlists.

### `ml/`
The core intelligence.
- `base_model.py`: Abstract base class for models.
- `predictor.py`: The high-level orchestrator for training and inference.
- `ensemble.py`: Logic for model arbitration.

### `data/`
- `provider.py`: Fetches data from Yahoo Finance and Finnhub.
- `cache.py`: Simple in-memory/disk caching to reduce API calls.

### `features/`
- `technical_indicators.py`: Vectorized calculation of RSI, MA, etc. using Pandas.
- `engineering.py`: Prepares feature sets for ML training.

## Key Design Patterns
- **Dependency Injection:** Services are instantiated and used across routes.
- **Serialization:** Models are persisted as `.pkl` files to avoid retraining on every request.
- **Streaming:** Support for Server-Sent Events (SSE) in AI chat responses.
- **Market Awareness:** Logic to detect IST (Indian Standard Time) market sessions for model staleness checks.
