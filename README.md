# Stock Intelligence Dashboard

A production-grade Stock Intelligence Dashboard that transforms financial time-series data into interactive analytics and machine-learning-powered predictive insights.

## Features

- **Real Stock Data**: Fetches live data from Yahoo Finance (US, Indian, and global stocks)
- **Technical Indicators**: MA7, MA21 moving averages with architecture for future indicators
- **ML Predictions**: Linear Regression and Random Forest models with confidence scores
- **Interactive Charts**: Plotly.js-powered price and volume charts with zoom, pan, and hover
- **Company Profiles**: Complete company information including sector, market cap, 52-week range
- **Watchlists**: Save and manage favorite stocks with Supabase persistence
- **Search History**: Track all searched tickers
- **Prediction History**: Store and retrieve all ML predictions
- **Responsive UI**: Mobile-first design with dark mode
- **Production Ready**: Full test coverage, API documentation, SpecKit specs

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- TailwindCSS
- Plotly.js
- TanStack Query
- Zustand

### Backend
- Python 3.11+
- FastAPI
- yfinance
- scikit-learn
- joblib
- Supabase

### Database
- Supabase (PostgreSQL with RLS)

## Project Structure

```
├── backend/
│   ├── api/
│   │   └── routes.py
│   ├── data/
│   │   ├── provider.py
│   │   └── cache.py
│   ├── features/
│   │   ├── engineering.py
│   │   └── technical_indicators.py
│   ├── ml/
│   │   ├── base_model.py
│   │   ├── linear_model.py
│   │   ├── random_forest_model.py
│   │   └── predictor.py
│   ├── schemas/
│   │   └── stock_schema.py
│   ├── services/
│   ├── database/
│   ├── tests/
│   └── main.py
├── src/
│   ├── components/
│   ├── pages/
│   ├── store/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   └── App.tsx
└── specs/
    └── 001-stock-intelligence-dashboard/
```

## Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload
```

### Environment Variables

Create `.env` file in the backend directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Usage

1. Open http://localhost:5173
2. Enter a stock ticker (e.g., AAPL, TCS.NS, GOOGL)
3. Click "Analyze" to fetch data and predictions
4. Toggle between Linear and Random Forest models
5. Change date range (1M, 6M, 1Y, 5Y)
6. Add stocks to your watchlist
7. View search history

## Supported Stocks

- **US**: AAPL, MSFT, GOOGL, NVDA, AMZN, TSLA, META
- **India**: TCS.NS, INFY.NS, RELIANCE.NS
- **Global**: Use format `SYMBOL.EXCHANGE`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/stock/{ticker} | Get stock data |
| POST | /api/v1/watchlist | Add to watchlist |
| GET | /api/v1/watchlist | Get watchlist |
| DELETE | /api/v1/watchlist/{id} | Remove from watchlist |
| GET | /api/v1/history | Get search history |
| DELETE | /api/v1/history | Clear history |
| GET | /api/v1/predictions | Get predictions |
| POST | /api/v1/predictions | Save prediction |

Full API documentation: http://localhost:8000/docs

## Testing

### Frontend Tests
```bash
npm run test
```

### Backend Tests
```bash
cd backend
pytest
```

## Building for Production

### Frontend
```bash
npm run build
```

### Backend
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Deployment

- Frontend: Deploy to Vercel
- Backend: Deploy to Render
- Database: Supabase (already hosted)

## ML Models

### Linear Regression
- Fast baseline model
- Interpretable coefficients
- Good for trend continuation

### Random Forest
- Ensemble of decision trees
- Captures non-linear relationships
- Feature importance analysis

### Features Used
- Close price
- Volume
- MA7, MA21
- Returns
- Lag features (5 days)
- Volume change

## Architecture Decisions

- **Zustand**: Lightweight state management without boilerplate
- **TanStack Query**: Automatic caching, background refetching
- **Plotly.js**: Rich interactivity, zoom/pan, hover tooltips
- **FastAPI**: Async, auto-docs, Pydantic validation
- **Supabase**: PostgreSQL reliability, RLS security

## Future Enhancements

- XGBoost, LSTM, Prophet models
- News sentiment analysis
- Portfolio analytics
- Candlestick charts
- User authentication
- WebSocket real-time data
- Multi-user support

## License

MIT
