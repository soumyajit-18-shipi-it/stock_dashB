# AGENTS.md: Codebase Intelligence for AI Agents

This document provides a high-level overview of the Stock Intelligence Dashboard architecture and implementation details to help future AI coding agents understand and modify the codebase efficiently.

## 🏗 System Architecture

The project follows a decoupled client-server architecture:

*   **Frontend:** React + Vite + Tailwind CSS + Zustand.
*   **Backend:** FastAPI (Python) + Scikit-Learn.
*   **Database:** Supabase (PostgreSQL + Auth).
*   **Data Providers:** Yahoo Finance (Prices), Finnhub (Company info/News).

## 📂 Repository Structure

```text
├── frontend/             # React UI
│   ├── src/components/   # Modular UI components
│   ├── src/services/     # API clients (api_client.ts)
│   ├── src/store/        # Zustand state management
│   └── src/hooks/        # Custom React hooks (useStock.ts)
├── backend/              # FastAPI Backend
│   ├── api/              # API routes (routes.py)
│   ├── services/         # Business logic (stock_service.py, etc.)
│   ├── ml/               # Machine learning models
│   ├── features/         # Feature engineering for ML
│   └── core/             # Core configuration (config.py)
├── supabase/             # Supabase configuration and migrations
└── specs/                # Project specifications and plans
```

## 🧠 Machine Learning Pipeline

1.  **Data Acquisition:** `Yahoo Finance` is used to fetch historical daily prices.
2.  **Feature Engineering:** Located in `backend/features/`. Includes:
    *   Technical indicators (RSI, Moving Averages).
    *   Volume lagging.
3.  **Model Training/Inference:** Located in `backend/ml/`.
    *   Models: `RandomForestRegressor`, `LinearRegression`.
    *   Models are trained on-the-fly or loaded from disk for inference.
4.  **Prediction:** Deterministic output based on historical patterns.

## ⚛️ Frontend State Management

We use **Zustand** for state management:
*   `stock_store.tsx`: Manages stock data, search history, and predictions.
*   `ui_store.ts`: Manages UI state (modals, drawers, loading states).

## 🔌 AI Providers & Streaming

*   The system is designed to support multiple AI providers (Gemini, OpenAI, etc.).
*   Configuration is managed in `frontend/src/services/aiProviderService.ts`.
*   Streaming responses are handled via Server-Sent Events (SSE) or standard REST with progressive UI updates.

## 🚀 Deployment

The repository includes configurations for:
*   **Railway:** `railway.json`
*   **Render:** `render.yaml`
*   **Vercel:** `vercel.json`
*   **Docker:** `Dockerfile` (Multi-stage build)

## 🛠 Quality & Compliance

*   **Linting:** Ruff (Python), ESLint (TypeScript).
*   **Formatting:** Ruff (Python), Prettier (TypeScript).
*   **Type Checking:** Mypy (Python), TSC (TypeScript).
*   **Security:** Bandit, Semgrep, Gitleaks.
*   **CI/CD:** GitLab CI (`.gitlab-ci.yml`).
