# Stock Intelligence Dashboard: Architecture

## High-Level Overview
The Stock Intelligence Dashboard is a multi-tier application designed for real-time stock analysis and machine learning-based price prediction. It leverages a Python FastAPI backend for heavy computation and ML inference, and a React frontend for data visualization and AI interactions.

## Core Components

### 1. Frontend (React + Vite + TypeScript)
- **Framework:** React 18 with TypeScript.
- **State Management:** Zustand for global application state (Stock, UI, Settings).
- **Data Fetching:** Tanstack Query (@tanstack/react-query) for caching and synchronizing backend data.
- **Visualization:** Plotly.js for interactive stock charts.
- **Internationalization:** i18next for multi-language support (EN, HI, OR, DE, FR).

### 2. Backend (FastAPI)
- **Framework:** FastAPI for high-performance asynchronous API endpoints.
- **Data Source:** Yahoo Finance (via requests/session) for historical data.
- **ML Engine:** Scikit-Learn (Linear Regression, Random Forest).
- **Orchestration:** Structured services for stock logic, watchlist management, and AI provider integration.

### 3. Persistence Layer (Supabase)
- **Database:** PostgreSQL hosted on Supabase.
- **Auth:** Supabase Auth for user management (integrated in the schema).
- **Storage:** Watchlists, search history, and prediction records.

### 4. Machine Learning
- **Models:** Ensemble of Linear Regression and Random Forest Regressor.
- **Feature Engineering:** Technical indicators (RSI, MA7, MA21, Lag features).
- **Arbitration:** Intelligent selection of the best-performing model based on confidence and market volatility.

## Data Flow
1. **User Request:** Search for a ticker (e.g., "AAPL").
2. **Frontend:** Updates store, triggers `useStock` query.
3. **Backend:**
   - Fetches historical OHLCV data.
   - Calculates 10+ technical indicators.
   - Runs inference on trained models.
   - Logs search to history.
4. **Response:** Unified `StockResponse` returned to the frontend.
5. **Visualization:** UI renders charts and prediction cards.

## Deployment
- **Frontend:** Vercel.
- **Backend:** Railway.
- **Database:** Supabase.
