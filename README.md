# 📈 Stock Intelligence Dashboard

A production-grade stock analysis and prediction platform powered by **Python FastAPI** and **React**.

## 🏆 Engineering Excellence & Compliance
This repository adheres to the highest standards of software quality and maintainability.

- **10/10 Pylint Score:** Backend code follows strict PEP 8 and professional coding standards.
- **Strict Mypy Type Safety:** 100% type coverage across the entire Python backend.
- **Modern Linting & Formatting:** Powered by **Ruff** for sub-millisecond linting and **Flake8** for standard compliance.
- **Security Scanned:** Automated security policy checks using **Semgrep** and **Gitleaks**.
- **Spec-Driven Development:** Initialized with **Spec-Kit** for robust architecture and planning.

## 🏗 Architecture
The system follows a **Single Backend Architecture** for high consistency and ML precision.

```mermaid
graph TD
    User((User)) -->|Search| React[React Frontend]
    React -->|REST API| FastAPI[FastAPI Backend]
    FastAPI -->|Market Data| Yahoo[Yahoo Finance API]
    FastAPI -->|Company Info| Finnhub[Finnhub API]
    FastAPI -->|Inference| ML[Scikit-Learn Models]
    React -->|Storage| Supabase[(Supabase DB)]
```

## 📂 Folder Structure
```text
├── .specify/             # Spec-Kit (Memory, Templates, Specs)
├── backend/              # Unified FastAPI Backend
│   ├── api/              # Endpoints & Routes
│   ├── services/         # Yahoo/Finnhub/Stock logic
│   ├── ml/               # Prediction Models (RF, Linear)
│   ├── features/         # Technical Indicator Engineering
│   ├── core/             # Config & Logging
│   └── tests/            # Integrated Unit & Integration Tests
├── frontend/             # React + Vite (UI Layer)
│   ├── src/services/     # API Clients
│   └── src/components/   # Data Visualization
└── run.py                # Root Entry Point
```

## 🚀 Setup & Installation

### 1. Environment Variables

Create a `.env` in the `backend/` folder:
```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
GOOGLE_AUTH_ENABLED=true
FINNHUB_API_KEY=your_finnhub_key
DEFAULT_GROQ_API_KEY=your-groq-key-or-leave-empty-for-ollama
```

Create a `.env` in the `frontend/` folder:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_URL=http://localhost:5173
VITE_ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
```

`VITE_API_URL` must point at the FastAPI backend: `http://localhost:8000/api/v1`.
Do not use `http://localhost:5173/api/v1` for backend requests. The Vite dev server
runs the frontend only.

### 2. Database Setup (No CLI Required)

To initialize the database schema in your Supabase Web Dashboard:
1. Open the root-level consolidated SQL file [supabase_setup.sql](file:///C:/Users/soumy/stock_dashB/supabase_setup.sql).
2. Copy its entire contents.
3. Open your **Supabase Web Dashboard** -> **SQL Editor** -> **New Query**.
4. Paste the SQL and click **Run**.

*Note: The local Supabase CLI is entirely optional. The primary, recommended setup path is running the consolidated SQL via the Web Dashboard SQL Editor.*

#### Web Dashboard Verification Check:
* Go to the **Table Editor** on your Supabase Web Dashboard.
* Confirm that the `public.user_profiles` and `public.feedback_issues` tables exist.
* Verify user signup tracking works by running `select count(*) as total_users from public.user_profiles;` in the SQL Editor.

### 3. Backend Setup (FastAPI)
```bash
python -m venv .venv
# Activate venv (Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate)
pip install -r backend/requirements.txt
python run.py
```
*Note:* The backend binds to `0.0.0.0:8000` internally, which is a bind address. To access the backend or API docs in your browser, navigate to:
* **Local Backend API:** [http://localhost:8000](http://localhost:8000)
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Frontend Setup (React)
```bash
cd frontend
npm install
npm run dev
```
Open **Local Frontend URL:** [http://localhost:5173](http://localhost:5173) in your browser.

### 5. Authentication Landing Gate
When first loading the frontend, users are greeted with a beautiful, secure Google Login landing page gate. Access to the main dashboard is restricted until a user logs in. The redirect callback is processed at `/auth/callback`.

The frontend sends `Authorization: Bearer <Supabase access token>` to protected
backend endpoints. It never sends the Supabase anon key, refresh token, or service
role key as a bearer token.

User-owned data is saved per Supabase authenticated user:
* Watchlist rows use `user_id = auth.users.id`.
* Search history rows use `user_id = auth.users.id`.
* Feedback rows use `user_id = auth.users.id`.
* Admin stats are available only when the authenticated email is in `ADMIN_EMAILS`.

### 6. Interactive UI Tools
The dashboard offers separate UI widgets at the bottom:
* **Ask AI:** Accessible via the Navbar or a floating bottom-right action button (`bottom-5`).
* **Report Issue / Request Feature:** Accessible via a smaller, clean dark button at the bottom-right (`bottom-20`), ensuring no overlap with core chart tools. If logged out, it prompts the user to log in with Google to submit reports.

Ask AI uses the backend AI proxy for app-default providers. If no Groq key is
configured and Ollama is not reachable, it returns: `AI provider is not configured.
Please set DEFAULT_GROQ_API_KEY or configure Ollama.` API keys remain backend-only
unless a user explicitly enters their own key in local browser settings.

Stock data uses Yahoo Finance for history/quote data and Finnhub plus Yahoo
fallbacks for company profile fields. Backend caches quote/profile/history and
reuses already-fetched history for predictions so profile failures do not block
price/chart rendering.

## 🧪 Quality Control & Testing
We use a comprehensive suite of tools to ensure stability:

```bash
# Run all tests with coverage
pytest --cov=backend --cov-report=xml

# Run linting checks
ruff check .
flake8 .
pylint backend

# Run type checking
mypy backend run.py
```

## 🔄 CI/CD Pipeline
The project features a full-lifecycle **GitLab CI** pipeline with the following stages:
1. **Format:** Ensures consistent code style (Ruff).
2. **Lint:** Validates PEP 8 and code quality (Flake8, Pylint).
3. **Type Check:** Enforces strict typing (Mypy).
4. **Security:** Scans for vulnerabilities (Semgrep, Gitleaks).
5. **Test:** Executes backend and frontend test suites.
6. **Coverage:** Generates and enforces test coverage (>80%).
7. **Build:** Creates production Docker images.
8. **Release:** Automated changelog generation and tagging.

## 🧠 ML Implementation
- **Models:** Random Forest Regressor & Linear Regression.
- **Feature Engineering:** Automated technical indicators (MA7, MA21, RSI, MACD, etc.).
- **Evaluation:** Real-time metrics (RMSE, MAE, R2) for every prediction.

## ⚠️ Known Issues
- **API Rate Limits:** Finnhub API limits apply to the free tier (60 calls/min).
- **Data Delay:** Yahoo Finance data may be delayed by 15-20 minutes for certain exchanges.

## 🔮 Future Improvements
- **Real-time Streaming:** Integration with WebSockets for live ticker updates.
- **Sentiment Analysis:** Adding news sentiment from Finnhub to the ML feature set.
- **Redis Caching:** Implementing a dedicated caching layer for high-traffic tickers.
