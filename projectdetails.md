# Stock Intelligence Dashboard — Project Details

---

## 1. Project Overview & Objective

### Project Title

**Stock Intelligence Dashboard** (also referred to as `stock_dashB` in the repository). The project name in code and configuration is **"Stock Intelligence Dashboard API"**.

### Problem Statement

- Investors and analysts lack a unified platform to analyze stocks with both traditional financial data and machine learning-driven predictions.
- Existing tools either provide raw data (Yahoo Finance) without advanced analytics or require complex, disconnected workflows.
- There is no integrated solution combining conversational AI, ML-based price prediction, watchlist management, and multi-language support in a single dashboard.

### Objective

- Provide a production-grade stock analysis and prediction platform powered by machine learning and real-time financial data.
- Use ensemble ML models (Linear Regression + Random Forest) to forecast stock price movements.
- Offer an AI-powered chat interface for conversational analysis of stock data.
- Automate feature engineering (technical indicators) for accurate predictions.
- Enable multi-language internationalization (English, Hindi, Odia, German, French).

---

## 2. System Architecture & Tech Stack

### Dataset

- **Source:** Yahoo Finance API (via yfinance library + direct HTTP fallback to `query1.finance.yahoo.com`).
- **Secondary Source:** Finnhub API for company profile data (industry, sector, country, exchange).
- **Preprocessing Steps:**
  - NaN/Infinity sanitization via `sanitize_value()`.
  - Timezone-aware DatetimeIndex conversion.
  - Data caching with TTL-based freshness (60s during market hours, 300s after close).
  - Fallback chain: `yfinance → direct Yahoo Finance API → error`.

### Algorithms / Models

| Model | Type | Library | Details |
|---|---|---|---|
| Linear Regression | Regression | scikit-learn | Pipeline with StandardScaler; train/test split 80/20 |
| Random Forest | Regression | scikit-learn | 200 estimators, max_depth=8, min_samples_leaf=5 |
| Ensemble Arbitration | Meta-algorithm | Custom (`ml/ensemble.py`) | Weighted average when models agree; confidence-based winner when they disagree |
| Confidence Scoring | Custom formula | `BaseModel.get_confidence_score()` | Blended: `((R²+1)/2) × (1 - min(RMSE/mean_price, 0.5))` |
| Technical Indicators | Feature Engineering | Custom (`features/`) | MA7, MA21, price lags (lag1–lag5), returns, volume change |

### Backend

| Component | Technology |
|---|---|
| Framework | FastAPI (Python 3.11) |
| Server | Uvicorn |
| Data Provider | yfinance 0.2.49 + httpx for Finnhub |
| ML | scikit-learn (joblib for model persistence) |
| Database | Supabase (PostgreSQL) with mock fallback |
| AI / LLM | Multi-provider: Groq (default), OpenAI, Anthropic, Gemini, Ollama, OpenRouter |
| Validation | Pydantic v2 / pydantic-settings |
| Async | httpx for external API calls |
| Testing | pytest, pytest-asyncio, pytest-cov |

**Authentication:** None implemented for API endpoints. Supabase RLS policies exist (migrated from authenticated-only to open anon access). No JWT/auth middleware on FastAPI.

### Frontend

| Component | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3 + custom CSS variables for theming |
| State Management | Zustand (`stock_store.tsx`, `ui_store.ts`) |
| Data Fetching | TanStack React Query 5 |
| Visualization | Plotly.js (react-plotly.js) |
| Internationalization | i18next (5 languages: EN, HI, OR, DE, FR) |
| PDF Export | jsPDF + html2canvas |
| Testing | Vitest, Testing Library, Playwright |

### Deployment

| Platform | Purpose |
|---|---|
| Render | Backend deployment (FastAPI) |
| Vercel | Frontend hosting with API calls to Render |
| Docker | Multi-stage Dockerfile (Node → Python → production image) |
| GitLab CI | Full CI/CD: format, lint, type_check, security (Semgrep, Gitleaks), test, coverage (>80%), build, release |
| Devcontainer | VS Code / GitHub Codespaces support (`.devcontainer/`) |

---

## 3. Methodology & Workflow

### Data Collection

- **Stock Data:** Yahoo Finance API via yfinance library. OHLCV (Open, High, Low, Close, Volume) daily candles.
- **Company Profile:** Finnhub API (`/stock/profile2`) for industry, sector, country. yfinance `fast_info` and `info` as primary/fallback.
- **AI Chat:** User-provided API keys or default Groq key. Supports Groq, OpenAI, Anthropic, Gemini, OpenRouter, Ollama.

### Data Preprocessing

1. **Sanitization:** Remove NaN, infinite, and null values via `sanitize_value()`.
2. **Timezone Handling:** Convert UTC timestamps to exchange timezone (`America/New_York` default).
3. **Feature Engineering** (`FeatureEngineer.prepare_features()`):
   - Add MA7, MA21 (moving averages).
   - Calculate daily returns (`Close.pct_change()`).
   - Create lag features (lag1 through lag5 of Close price).
   - Calculate volume change (`Volume.pct_change()`).
   - Drop NaN rows.
4. **Caching:** In-memory cache with TTL based on market hours vs. closed.

### Model Training

- **No explicit training pipeline exists.** Models are trained on-the-fly during prediction requests.
- **Training Trigger:** First prediction request for a given (ticker, range) pair, or when cached `.pkl` is stale.
- **Staleness Logic** (`_model_is_stale()`):
  - If today's NSE session has ended and the model was written before session close → retrain.
  - Session times: 09:15–15:30 IST.
- **Train/Test Split:** 80/20, chronologically (no shuffle).
- **Model Persistence:** joblib `.pkl` files stored in `backend/models/`. Filename format: `{ticker}_{range}_{model}.pkl` (e.g., `aapl_1y_linear.pkl`).

### System Workflow

1. **User Interaction:** User enters a stock ticker in the search bar (e.g., "AAPL") or selects from quick tickers / watchlist.
2. **Frontend Processing:**
   - SearchBar updates Zustand store (`setTicker`).
   - `useStock` query hook triggers `api.getStock()` call.
   - Watchlist / History data loaded on mount.
3. **Backend Processing** (`GET /api/v1/stock/{ticker}`):
   - `HistoryService`: Logs search to Supabase `search_history`.
   - `StockService.get_full_stock_analysis()`:
     - Fetch OHLCV data from Yahoo Finance.
     - Fetch company profile from Finnhub + yfinance.
     - Merge profile data with fallbacks.
     - Compute technical indicators (MA7, MA21).
     - Run ML prediction (train or load model).
4. **AI Execution (Optional):**
   - User opens AI chat drawer → messages sent to `/api/v1/ai/chat`.
   - Backend streams response via SSE with provider fallback chain.
   - For report generation, `generateReport()` sends structured prompt to AI.
5. **Database Operations:**
   - Supabase tables: `watchlists`, `search_history`, `predictions`, `users`, `saved_models`.
   - `MockSupabaseClient` used when credentials are missing (local dev).
6. **Response Generation:**
   - `StockResponse` returned as JSON → Plotly charts render (price + volume).
   - `PredictionCard` shows confidence, trend, metrics (RMSE, MAE, R²).

#### Mermaid Flowchart

```mermaid
graph TD
    User((User)) -->|Search Ticker| SearchBar[SearchBar Component]
    SearchBar -->|setTicker| Zustand[Zustand Store]
    Zustand -->|Triggers| useStock[useStock Hook]
    useStock -->|GET /api/v1/stock/{ticker}| FastAPI[FastAPI Backend]
    FastAPI -->|OHLCV Data| Yahoo[Yahoo Finance API]
    FastAPI -->|Company Profile| Finnhub[Finnhub API]
    FastAPI -->|Save to| Supabase[(Supabase DB)]
    FastAPI -->|Train/Predict| ML[scikit-learn Models]
    FastAPI -->|StockResponse| React[React Frontend]
    React -->|Plotly| Charts[Price + Volume Charts]
    React -->|PredictionCard| Prediction[Price Prediction]
    React -->|AI Chat| AI[AI Provider /api/v1/ai/chat]
    AI -->|SSE Stream| ChatDrawer[Ask AI Drawer]
    React -->|Export Report| PDF[jsPDF Report]
```

---

## 4. ML Pipeline Specifics

### Feature Engineering

**File:** `backend/features/engineering.py`

| Feature | Formula / Implementation | Code Location |
|---|---|---|
| `ma7` | `Close.rolling(window=7).mean()` | `technical_indicators.py:25` |
| `ma21` | `Close.rolling(window=21).mean()` | `technical_indicators.py:26` |
| `returns` | `Close.pct_change()` | `engineering.py:12` |
| `lag1` | `Close.shift(1)` | `engineering.py:13` |
| `lag2` | `Close.shift(2)` | `engineering.py:14` |
| `lag3` | `Close.shift(3)` | `engineering.py:15` |
| `lag4` | `Close.shift(4)` | `engineering.py:16` |
| `lag5` | `Close.shift(5)` | `engineering.py:17` |
| `volume_change` | `Volume.pct_change()` | `engineering.py:18` |
| `Close` | Original closing price | Passed through |
| `Volume` | Original volume | Passed through |

All NaN rows are dropped via `df.dropna()` at the end of `prepare_features()`.

**Additional indicators computed but NOT included in ML features (chart only):**
- EMA (`calculate_ema` in `technical_indicators.py:31`) — exists as a utility, not called from feature engineering.
- RSI (`calculate_rsi` in `technical_indicators.py:35`) — exists as a utility, not called anywhere in the pipeline.

**Explicitly missing** (present in the docs but NOT implemented): MACD, Bollinger Bands, SMA (beyond MA7/MA21).

**Feature columns for training** (`get_feature_columns()`):
```python
["Close", "Volume", "ma7", "ma21", "returns",
 "lag1", "lag2", "lag3", "lag4", "lag5", "volume_change"]
```

### Ensemble Model Logic

**File:** `backend/ml/ensemble.py`

- **If both models agree** (both predict UP or both DOWN):
  - **Weighted average:** `predicted = w_lin × linear_price + w_rf × rf_price`
  - Weights are relative confidence: `w_lin = linear_confidence / (linear_confidence + rf_confidence)`
  - Blended confidence: `linear_confidence × w_lin + rf_confidence × w_rf`
  - `model_used = "ensemble"`

- **If models disagree** (one predicts UP, one DOWN):
  - The model with the higher confidence score wins outright.
  - The loser is discarded entirely.
  - `model_used = "linear"` or `"random_forest"` (the winner).

- **Low confidence flag:** If `abs(linear_confidence - rf_confidence) < 0.05`, the result is flagged as `low_confidence = True`.

There is **no meta-model, no stacking, no bagging** beyond the RF itself.

### Prediction Target

**Files:** `backend/ml/predictor.py:157-193` and `backend/features/engineering.py:41`

- **Target variable:** `y = df["Close"].shift(-1)` — predict the **next-day closing price**.
- **Prediction horizon:** 1 day ahead.
- After training, `predictor.py:173-174` calls `prepare_prediction_input(df)` which takes the **last** row of the feature DataFrame and feeds it to the model.
- The prediction is a single float: the next-day closing price.
- `TrendDirection` (INCREASE / DECREASE) is derived by comparing `predicted_price > last_close`.

---

## 5. BYOK AI Chat

### How Bring Your Own Key Works

**Files:**
- **Frontend:** `frontend/src/components/AISettingsModal.tsx`
- **Frontend Service:** `frontend/src/services/aiProviderService.ts`
- **Backend:** `backend/services/ai_service.py`

**Flow:**

1. User opens AI Settings modal (gear icon in navbar).
2. User selects provider: **Ollama** (local) or **Auto-Detect / App Default**.
3. If Ollama: user enters a base URL (default `http://localhost:11434`). No API key needed.
4. If Auto: user can paste an API key (optional) and optionally a custom base URL.
   - If left blank, the backend uses its **default Groq API key** from `DEFAULT_GROQ_API_KEY` env var.
5. Key is **stored in localStorage** under `ai_provider_config` (`frontend/src/store/ui_store.ts:77`).
6. Key is **NOT stored in Supabase** and **NOT stored on the backend** — only passed per-request.
7. When a chat request is made, the key is sent to the backend in the POST body:
   ```typescript
   body: JSON.stringify({
     messages, provider, model: config.selectedModel,
     api_key: config.apiKey, base_url: baseUrl, stream: true
   })
   ```
8. Backend receives the key and uses it for that request only.

### Supported LLM Providers

| Provider | Default Model | Default Base URL |
|---|---|---|
| **Groq** (default) | `llama-3.3-70b-versatile` | `https://api.groq.com/openai/v1` |
| **OpenAI** | `gpt-4o-mini` | `https://api.openai.com/v1` |
| **Anthropic** | `claude-3-5-sonnet-20240620` | `https://api.anthropic.com/v1` |
| **Gemini** | `gemini-1.5-flash` | `https://generativelanguage.googleapis.com/v1` |
| **OpenRouter** | (falls back to OpenAI default) | `https://openrouter.ai/api/v1` |
| **Ollama** | `llama3` | `http://localhost:11434` |

### Fallback Chain

If the primary provider fails, the backend tries in order:
1. Primary provider (user-selected).
2. Ollama (local, if available).
3. Groq with default app key (if different from primary).

### AI Chat Capabilities

- **Conversational Q&A** about stocks — user asks free-form questions, model responds with stock context injected in the system prompt.
- **PDF Report Generation** — 11-section equity research report: Executive Summary, Company Information, Price Analysis, Technical Analysis, Prediction Analysis, Bullish Factors, Bearish Factors, Risk Assessment, Scenario Analysis, Recommendation, Conclusion.
- **Markdown Rendering** — headers, bold, italic, code blocks, lists, blockquotes, tables.
- **Chat History Persistence** — per-ticker conversation history saved in localStorage.
- **Export** — conversations exported as `.txt` files.

The **system prompt** injects: ticker, company name, exchange, sector, industry, current price, prediction (price + trend + confidence), ML metrics (RMSE, MAE, R²), and last 15 candles of historical data.

---

## 6. Supabase Usage

### Database Schema

**File:** `supabase/migrations/20260610044702_001_initial_schema.sql`

| Table | Columns | Purpose |
|---|---|---|
| `users` | `id` (UUID PK), `email` (TEXT UNIQUE), `created_at` (TIMESTAMPTZ) | Extends Supabase auth.users |
| `watchlists` | `id` (UUID PK), `user_id` (UUID FK→users), `ticker` (TEXT NOT NULL), `name` (TEXT), `created_at` (TIMESTAMPTZ) | User's watched stock tickers |
| `search_history` | `id` (UUID PK), `user_id` (UUID FK→users), `ticker` (TEXT NOT NULL), `searched_at` (TIMESTAMPTZ) | Ticker search history per user |
| `predictions` | `id` (UUID PK), `ticker` (TEXT NOT NULL), `model` (TEXT), `predicted_price` (DECIMAL 18,4), `actual_price` (DECIMAL 18,4), `confidence` (DECIMAL 5,4), `created_at` (TIMESTAMPTZ) | Stored prediction records |
| `saved_models` | `id` (UUID PK), `model_name` (TEXT UNIQUE NOT NULL), `file_path` (TEXT NOT NULL), `updated_at` (TIMESTAMPTZ) | Metadata about persisted ML models |

**Row Level Security (RLS):** The second migration (`20260610052130_002_allow_anon_access.sql`) opened all tables to **anon** and **authenticated** users with `USING (true)` policies — effectively public access.

### What Supabase Does NOT Store

- Historical stock prices (stored in-memory cache only).
- API keys (stored in localStorage or passed in request body).
- Chat history (stored in localStorage).
- Portfolio information.
- Active authentication sessions (schema exists but login/signup is not implemented in the app).

### Mock Fallback

When credentials are placeholders, `MockSupabaseClient` (`backend/database/supabase_client.py:143-145`) provides in-memory stores for `watchlists`, `search_history`, and `predictions`.

### Supabase Edge Function

**File:** `supabase/functions/stock-analysis/index.ts` — **Deprecated.** Returns HTTP 410 with instructions to use the FastAPI backend instead.

---

## 7. ML Performance Metrics

### Metrics Computed During Training

**File:** `backend/ml/base_model.py:56-83`

| Metric | Formula | Code Location |
|---|---|---|
| **RMSE** | `sqrt(mean_squared_error(y_true, y_pred))` | `base_model.py:72` |
| **MAE** | `mean_absolute_error(y_true, y_pred)` | `base_model.py:73` |
| **R²** | `r2_score(y_true, y_pred)` | `base_model.py:74` |

### Confidence Score

**File:** `backend/ml/base_model.py:85-102`

```python
r2_component = (r2 + 1) / 2             # maps [-1, 1] → [0, 1]
relative_rmse = rmse / mean_price        # dimensionless
rmse_penalty = min(relative_rmse, 0.5)   # cap at 0.5
score = r2_component * (1.0 - rmse_penalty)
```

### What Users See

**File:** `frontend/src/components/PredictionCard.tsx:58-71`

PredictionCard displays:
- RMSE (2 decimal places)
- MAE (2 decimal places)
- R² (3 decimal places)
- Confidence as a percentage with a progress bar

### What's NOT Present

- No evaluation scripts or separate validation datasets beyond the 80/20 train-test split.
- No directional accuracy metric.
- No precision, recall, F1 score (not applicable to regression).
- No backtesting framework.
- No logged metric history — metrics are stored ephemerally in model objects, not persisted.
- No notebooks with evaluation outputs.
- Concrete metric values are not hardcoded or documented — they vary per training run.

---

## 8. Deployment Architecture

### Services Summary

| Platform | Hosts | Details |
|---|---|---|
| **Render** | FastAPI Backend | `render.yaml` — service `stock-dashboard-backend`, start command `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers` |
| **Vercel** | React Frontend | `vercel.json` — builds frontend with `VITE_API_URL` pointing to the Render backend |
| **Docker** | Combined (multi-stage) | Multi-stage: builds frontend (node:18), then Python backend (python:3.11-slim) |

### Docker Architecture

**File:** `Dockerfile`

Three stages:
1. **frontend-builder** (node:18-alpine): `npm install` + `npm run build` → produces `frontend/dist`
2. **backend-builder** (python:3.11-slim): `pip install -r requirements.txt` → outputs installed packages
3. **Final** (python:3.11-slim):
   - Copies frontend dist, backend code, and installed packages
   - Exposes port **8000**
   - Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### CI/CD Pipeline

**File:** `.gitlab-ci.yml`

8 stages, sequential:

1. **format** — ruff (Python) + prettier check (Frontend)
2. **lint** — flake8 + pylint (Python) + eslint (Frontend)
3. **type_check** — mypy (Python) + tsc (Frontend)
4. **security** — Semgrep + Gitleaks
5. **test** — pytest (Python) + vitest (Frontend)
6. **coverage** — pytest-cov (minimum 80%, Cobertura XML report)
7. **build** — Docker build (only on `main` branch)
8. **release** — git-cliff changelog generation (only on tags)

### Ports & Startup Commands

| Service | Port | Startup Command |
|---|---|---|
| Render | `$PORT` | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers` |
| Docker | 8000 | `uvicorn backend.main:app --host 0.0.0.0 --port 8000` |
| Local dev | 8000 (default) | `uvicorn backend.main:app --reload` |

### Frontend–Backend Communication

**File:** `vercel.json:4-8`

```json
{
  "source": "/api/(.*)",
  "destination": "https://stock-dashb.onrender.com/api/v1/:path*"
}
```

The frontend uses the `VITE_API_URL` env var. In production it points to `https://stock-dashb.onrender.com/api/v1`; locally it can point to `http://localhost:8000/api/v1`.

### Environment Variables

| Variable | Source | Required? |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | Required for real DB |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service key | Required for real DB |
| `FINNHUB_API_KEY` | Finnhub API | Optional (profile data degrades) |
| `DEFAULT_GROQ_API_KEY` | Groq Console | Optional (AI chat falls back) |
| `OPENAI_API_KEY` | OpenAI | Optional |
| `GEMINI_API_KEY` | Google AI | Optional |
| `ANTHROPIC_API_KEY` | Anthropic | Optional |
| `OPENROUTER_API_KEY` | OpenRouter | Optional |
| `CORS_ORIGINS` | Config | Explicit frontend/local origins |
| `HOST` | Config | Defaults to `0.0.0.0` |
| `PORT` | Config | Defaults to `8000` |
| `VITE_API_URL` | Frontend | Render `/api/v1` URL in production |

### Architecture Diagram

```
User Browser
    │
    ▼
Vercel (React SPA) ──── HTTPS API calls ────→ Render (FastAPI Backend)
    │                                                   │
    ▼                                                   ▼
localStorage                                        Supabase (PostgreSQL)
  • Watchlist                                        Yahoo Finance API
  • Chat History                                     Finnhub API
  • AI Config                                        AI Providers
  • Theme, Language                                  (Groq/OpenAI/...)
```

---

## 9. Features Summary

| Feature | Description |
|---|---|
| **Stock Search** | Real-time search with auto-suggest, recent history, and quick tickers (AAPL, MSFT, GOOGL, TSLA, NVDA, RELIANCE.NS) |
| **Price Chart** | Interactive Plotly chart with MA7/MA21 overlays |
| **Volume Chart** | Bar chart of trading volume with green/red coloring |
| **ML Prediction** | Price prediction with confidence, trend direction, model metrics |
| **Company Profile** | Sector, industry, market cap, 52-week high/low, exchange, currency |
| **Watchlist** | Add / remove stocks with live price sparklines and change percentages |
| **Search History** | Recent searches persisted locally |
| **AI Chat** | Conversational AI drawer with provider selection (6 providers) |
| **AI Report** | PDF export of structured equity research report (11 sections) |
| **Multi-Language** | English, Hindi, Odia, German, French |
| **Dark / Light Mode** | Persistent theme toggle with CSS variable system |
| **Date Range Selector** | 1M, 6M, 1Y, 5Y |
| **Model Toggle** | Linear Regression vs Random Forest |

---

## 10. API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root welcome message |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/stock/{ticker}` | Full stock analysis |
| `GET` | `/api/v1/watchlist` | Get watchlist |
| `POST` | `/api/v1/watchlist/{ticker}` | Add to watchlist |
| `DELETE` | `/api/v1/watchlist/{ticker}` | Remove from watchlist |
| `GET` | `/api/v1/history` | Get search history |
| `DELETE` | `/api/v1/history` | Clear search history |
| `GET` | `/api/v1/predictions` | Get saved predictions |
| `POST` | `/api/v1/predictions` | Save prediction |
| `POST` | `/api/v1/ai/chat` | AI chat (streaming SSE) |
| `GET` | `/api/v1/ai/models` | Get available AI models |
| `POST` | `/api/v1/ai/test` | Test AI connection |

---

## 11. Practical Applications & Future Scope

### Real-World Impact

- **Individual Investors:** Access ML-powered price predictions without quantitative finance expertise.
- **Traders:** Monitor watchlists with live price changes and technical indicators.
- **Financial Analysts:** Generate structured equity research reports with AI assistance.
- **Students / Researchers:** Learn about ensemble ML methods applied to financial time series.
- **Multi-lingual Users:** Native-language support for Hindi, Odia, German, and French speakers.

### Future Enhancements

- **Real-time WebSocket Streaming:** Replace polling with live ticker updates via WebSockets.
- **Sentiment Analysis:** Integrate Finnhub news sentiment as an ML feature.
- **Redis Caching:** Dedicated caching layer for high-traffic tickers.
- **User Authentication:** Activate Supabase Auth with proper JWT validation on API endpoints.
- **Prediction History Dashboard:** Visualize historical prediction accuracy vs. actual prices.
- **Backtesting Framework:** Evaluate model performance on historical data systematically.
- **Portfolio Management:** Track multiple holdings with aggregated performance metrics.
- **Additional Data Providers:** Add Alpha Vantage, IEX Cloud, or other sources as fallbacks.

---

## 12. PPT-Ready Summary

### Stock Intelligence Dashboard

- **Objective:** ML-powered stock analysis & prediction platform with conversational AI.
- **Tech Stack:**
  - **Backend:** Python FastAPI, scikit-learn, Supabase
  - **Frontend:** React 18, TypeScript, Tailwind CSS, Plotly.js
  - **AI:** Multi-provider (Groq, OpenAI, Anthropic, Gemini, Ollama)
- **ML Pipeline:**
  - Ensemble: Linear Regression + Random Forest with confidence-based arbitration
  - Features: MA7, MA21, lag variables, returns, volume change
  - On-the-fly training with model caching (`.pkl`)
- **Key Features:**
  - Interactive price / volume charts with technical indicators
  - ML price prediction with confidence scoring
  - Conversational AI chat drawer for stock analysis
  - PDF equity research report generation
  - Multi-language (EN, HI, OR, DE, FR)
  - Watchlist with live sparklines
- **Deployment:** Render (API), Vercel (UI), Docker, GitLab CI
- **Metrics:** RMSE, MAE, R² displayed; CI enforces >80% test coverage
- **Practical Use:** Individual investors, financial analysts, traders, finance students
- **Future:** WebSocket streaming, portfolio tracking, backtesting engine, news sentiment integration
