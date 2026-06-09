📊 Stock Intelligence Dashboard

A full-stack, AI-powered stock analysis platform that combines real-time financial data visualization with machine learning-based price prediction. Built using React (frontend) and FastAPI (backend) with a modular ML pipeline.

🚀 Overview

The Stock Intelligence Dashboard allows users to:

Analyze historical stock market trends
View interactive financial charts
Generate next-day stock price predictions using ML models
Explore company-level financial information

The system integrates data fetching, feature engineering, visualization, and machine learning into a single seamless workflow.

🧠 Key Features
📈 Stock Data Visualization
Interactive Plotly charts for:
Closing price trends
Trading volume
Moving averages (7-day, 21-day)
Dynamic updates based on user input
🤖 Machine Learning Prediction
Predicts next-day stock closing price
Models supported:
Linear Regression (baseline)
Random Forest Regressor (advanced option)
Outputs:
Predicted price
Trend direction (Increase / Decrease)
🏢 Company Insights
Company name
Sector / industry
Market capitalization
52-week high and low
🏗️ System Architecture
Frontend (React + TypeScript)
        ↓
API Client (Axios/Fetch)
        ↓
Backend (FastAPI)
        ↓
Data Layer (yfinance)
        ↓
Feature Engineering (Pandas)
        ↓
Machine Learning (Scikit-learn)
        ↓
JSON Response
        ↓
Frontend Visualization (Plotly)
⚙️ Tech Stack
Frontend
React + TypeScript
Tailwind CSS
Plotly.js
Context API (State Management)
Backend
FastAPI
Uvicorn
yfinance
Data Processing
Pandas
NumPy
Machine Learning
Scikit-learn
Linear Regression
Random Forest Regressor
📁 Project Structure
stock-dashboard/
│
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── context/          # Global state
│   │   ├── services/         # API client
│   │   └── pages/            # Dashboard UI
│
├── backend/                  # FastAPI backend
│   ├── api/                  # API routes
│   ├── data/                # Data provider (yfinance)
│   ├── features/            # Feature engineering
│   ├── ml/                  # ML models
│   ├── schemas/             # Pydantic models
│   └── main.py              # Entry point
│
└── README.md
🔄 Data Flow
User Input (Stock Symbol)
        ↓
Frontend (React UI)
        ↓
API Request (/api/v1/stock/{ticker})
        ↓
Backend (FastAPI)
        ↓
yfinance (Stock Data Retrieval)
        ↓
Feature Engineering (MA7, MA21, Lag Features)
        ↓
Machine Learning Model
        ↓
Prediction + Processed Data
        ↓
Frontend Visualization (Plotly Charts)
▶️ How to Run
1. Clone Repository
git clone <repo-url>
cd stock-dashboard
2. Run Backend
cd frontend
python -m backend.main

Backend runs at:

http://localhost:8000
3. Run Frontend
cd frontend
npm install
npm run dev

Frontend runs at:

http://localhost:5173
🔍 API Endpoints
Health Check
GET /api/v1/health

Response:

{ "status": "ok" }
Stock Data + Prediction
GET /api/v1/stock/{ticker}?range=1y&model=linear

Example:

/api/v1/stock/AAPL?range=1y&model=rf
📊 ML Pipeline
Fetch historical stock data (yfinance)
Generate technical indicators:
Moving averages (7-day, 21-day)
Lag features
Train regression model:
Linear Regression (baseline)
Random Forest (optional)
Predict next-day closing price
Classify trend (Increase / Decrease)
🎯 Success Criteria
✔ Stock data loads correctly
✔ Charts update dynamically
✔ ML predictions are generated
✔ Frontend and backend communicate properly
✔ System runs end-to-end without errors
💡 Future Improvements
Add LSTM-based deep learning model
Include news sentiment analysis
Deploy backend (Render / AWS)
Add authentication system
Add portfolio tracking feature
🧑‍💻 Author

Built as a learning project combining:

Data Science
Machine Learning
Full-stack Web Development