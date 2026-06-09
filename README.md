# Stock Intelligence Dashboard

A full-stack, spec-driven stock analysis platform that combines financial data visualization with machine learning-based price prediction.

Built using React (frontend) and FastAPI (backend), it transforms raw stock market data into interactive charts and predictive insights.

---

## Overview

The system allows users to:

- Search any stock ticker (e.g., AAPL, INFY.NS)
- View historical price charts
- Analyze technical indicators (Moving Averages)
- Get next-day price prediction using ML models
- View company profile information

It follows a structured development lifecycle:

Specification → Planning → Task Breakdown → Implementation

---

## System Architecture

### Frontend (React + TypeScript)

Responsible for UI and visualization:

- Stock search input
- Interactive dashboard layout
- Plotly charts (price + volume)
- Prediction display panel
- Company profile section

Communicates with backend via:

http://localhost:8000/api/v1/stock/{ticker}

---

### Backend (FastAPI + ML Pipeline)

Modular architecture:

- api/ → REST endpoints
- data/ → Stock data fetching (yFinance)
- features/ → Technical indicators and feature engineering
- ml/ → Machine learning models
- schemas/ → API data contracts (Pydantic)

---

## Data Flow

1. User enters stock ticker (e.g., AAPL)
2. Frontend sends request to backend
3. Backend fetches data from yFinance
4. Feature engineering is applied:
   - Moving Averages (7-day, 21-day)
   - Lag features
5. ML model predicts next-day price
6. Response returned as structured JSON
7. Frontend renders:
   - Charts
   - Prediction
   - Company details

---

## API Endpoints

### Health Check

GET /api/v1/health

Response:
{
  "status": "ok"
}

---

### Stock Data

GET /api/v1/stock/{ticker}?range=1y&model=linear

Parameters:
- ticker → Stock symbol (AAPL, TCS.NS)
- range → 1m | 6m | 1y | 5y
- model → linear | rf

Response:
{
  "ticker": "AAPL",
  "profile": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "market_cap": 4396219367424,
    "high_52w": 317.4,
    "low_52w": 195.07
  },
  "history": [],
  "prediction": {
    "model": "Linear Regression",
    "predicted_price": 210.5,
    "trend": "increase",
    "current_price": 208.1
  }
}

---

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Plotly.js

### Backend
- FastAPI
- Uvicorn
- yFinance
- Pandas
- NumPy
- Scikit-learn

---

## Machine Learning

Two models are supported:

Linear Regression
- Fast and interpretable
- Baseline forecasting model

Random Forest Regressor
- Better for non-linear patterns
- More robust predictions

---

## Feature Engineering

- Moving Average (7-day)
- Moving Average (21-day)
- Lag features (t-1 to t-5)
- Day of week
- Month

---

## How to Run

### Backend

cd stock-dashboard
python -m backend.main

Backend runs at:
http://localhost:8000

---

### Frontend

cd frontend
npm install
npm run dev

Frontend runs at:
http://localhost:5173

---

## Testing API

Health check:
curl http://localhost:8000/api/v1/health

Stock data:
curl "http://localhost:8000/api/v1/stock/AAPL?range=1m&model=linear"

---

## Project Status

- Backend API complete
- ML pipeline integrated
- Frontend dashboard complete
- End-to-end system functional

Optional Improvements:
- Add LSTM / XGBoost models
- Add caching layer (Redis)
- Add authentication system
- Add real-time WebSocket updates

---

## Summary

This project is a complete end-to-end stock intelligence system that converts raw financial data into predictive insights using machine learning and interactive visualization.