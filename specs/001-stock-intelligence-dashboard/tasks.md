# Tasks Checklist

## Core Features

### Stock Data
- [x] Integrate yfinance for real stock data
- [x] Support US stocks (AAPL, MSFT, etc.)
- [x] Support Indian stocks (TCS.NS, INFY.NS)
- [x] Support global stocks
- [x] OHLCV data retrieval
- [x] Company profile data

### Technical Indicators
- [x] MA7 implementation
- [x] MA21 implementation
- [x] Feature engineering pipeline
- [ ] EMA support (future)
- [ ] RSI support (future)
- [ ] MACD support (future)
- [ ] Bollinger Bands (future)

### Machine Learning
- [x] Linear Regression model
- [x] Random Forest model
- [x] Model training
- [x] Model persistence
- [x] Model metrics (RMSE, MAE, R²)
- [x] Confidence scoring
- [ ] XGBoost support (future)
- [ ] LSTM support (future)
- [ ] Prophet support (future)

### Charts
- [x] Price chart with Plotly
- [x] Volume chart
- [x] MA7 overlay
- [x] MA21 overlay
- [x] Interactive hover tooltips
- [x] Zoom and pan
- [ ] Candlestick chart (future)

### User Interface
- [x] Search bar
- [x] Date range selector (1M, 6M, 1Y, 5Y)
- [x] Model toggle
- [x] Company profile card
- [x] Prediction card
- [x] Watchlist panel
- [x] Loading skeletons
- [x] Error handling
- [x] Responsive design
- [x] Dark mode support

### Database
- [x] Supabase tables created
- [x] RLS policies configured
- [x] Watchlist CRUD
- [x] Search history
- [x] Predictions storage

### API
- [x] GET /api/v1/health
- [x] GET /api/v1/stock/{ticker}
- [x] POST /api/v1/watchlist
- [x] GET /api/v1/watchlist
- [x] DELETE /api/v1/watchlist/{id}
- [x] GET /api/v1/history
- [x] GET /api/v1/predictions
- [x] POST /api/v1/predictions

### Testing
- [x] Backend unit tests
- [x] Backend integration tests
- [x] Frontend store tests
- [ ] E2E tests (future)

### Documentation
- [x] SpecKit specification
- [x] API documentation
- [x] README
- [ ] Deployment guide

## Performance
- [x] Data caching
- [x] Model persistence
- [x] Query optimization
- [ ] CDN for static assets (production)

## Security
- [x] RLS enabled
- [x] Environment variables
- [x] CORS configured
- [ ] Rate limiting (future)
- [ ] Authentication (future)
