# Quickstart Guide

## Prerequisites

- Node.js 18+
- Python 3.11+
- Supabase account

## Environment Setup

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Backend (backend/.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Installation

### Frontend
```bash
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Running Tests

### Frontend
```bash
npm run test
```

### Backend
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

## Usage

1. Open browser to http://localhost:5173
2. Enter a stock ticker (e.g., AAPL, TCS.NS)
3. Click Analyze to view stock data and predictions
4. Toggle between Linear Regression and Random Forest models
5. Add stocks to watchlist
6. View search history

## Stock Examples

- US Stocks: AAPL, MSFT, GOOGL, NVDA, AMZN, TSLA, META
- Indian Stocks: TCS.NS, INFY.NS, RELIANCE.NS
- International: Use format SYMBOL.EXCHANGE

## Troubleshooting

### Backend not connecting to Supabase
- Check environment variables
- Verify Supabase project is active

### Charts not loading
- Check console for errors
- Verify backend is running
- Check API endpoint

### Predictions not accurate
- Models need training data
- More historical data = better accuracy
- Try different date ranges

## API Documentation

Access interactive API docs at: http://localhost:8000/docs
