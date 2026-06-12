# Stock Intelligence Dashboard Specification

## Overview

A production-grade Stock Intelligence Dashboard that transforms financial time-series data into interactive analytics and machine-learning-powered predictive insights.

## Core Features

### P1: Basic Stock Analysis
- Search ticker symbols
- View historical OHLCV (Open, High, Low, Close, Volume) data
- Interactive price charts with Plotly.js

### P2: Technical Indicators
- Moving Average 7-day (MA7)
- Moving Average 21-day (MA21)
- Architecture supports future indicators: EMA, RSI, MACD, Bollinger Bands

### P3: ML Predictions
- Linear Regression baseline model
- Random Forest predictive model
- Model switching capability
- Predicted price display
- Trend direction (increase/decrease)
- Confidence score

### P4: Company Context
- Company name and metadata
- Sector and industry information
- Market capitalization
- Current price and previous close
- 52-week high/low range
- Exchange and country information

### P5: Watchlists
- Save stocks to watchlist
- Remove stocks from watchlist
- Persistent storage in Supabase

### P6: Search History
- Track searched tickers
- Timestamp for each search
- Supabase persistence

### P7: Predictions History
- Store all predictions
- Track model used
- Record confidence scores
- Supabase persistence

## Data Source

Primary: Yahoo Finance via yfinance Python library
- Supports US stocks (AAPL, MSFT, GOOGL, etc.)
- Supports Indian stocks (TCS.NS, INFY.NS, RELIANCE.NS)
- Global stock market coverage

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite build tool
- TailwindCSS styling
- Plotly.js for charts
- TanStack Query for data fetching
- Zustand for state management
- Lucide React for icons

### Backend
- Python 3.11+
- FastAPI framework
- yfinance for stock data
- scikit-learn for ML
- joblib for model persistence
- Supabase Python client

### Database
- Supabase (PostgreSQL)
- Row Level Security (RLS)
- Tables: users, watchlists, search_history, predictions, saved_models

## Performance Requirements

- Data retrieval under 3 seconds
- API response under 200ms after data fetch
- Smooth chart rendering
- Support 5 years of historical data
- Client-side caching for frequently searched tickers

## Security

- RLS enabled on all database tables
- User-scoped data access
- No hardcoded credentials
- Environment variable configuration
