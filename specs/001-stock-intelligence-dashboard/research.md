# Research Notes

## Data Sources Research

### Yahoo Finance (yfinance)
- Free, reliable stock data API
- Supports US and international markets
- Provides OHLCV data, company info, and metadata
- No rate limiting for reasonable usage
- Historical data up to 50+ years

### Technical Indicators Research
- Moving Averages: Simple, weighted, exponential
- MA7: Short-term trend indicator
- MA21: Medium-term trend indicator
- Cross signals: MA7 crossing MA21 signals trend changes

### ML Model Research
- Linear Regression: Fast, interpretable baseline
- Random Forest: Handles non-linear relationships, feature importance
- Feature engineering critical for performance
- Lag features capture momentum
- Moving averages help smooth noise

## Architecture Decisions

### State Management: Zustand
- Lightweight, ~1KB
- No boilerplate
- TypeScript friendly
- Simple DX compared to Redux

### Data Fetching: TanStack Query
- Automatic caching
- Background refetching
- Error handling
- Loading states

### Charts: Plotly.js
- Rich interactivity
- Zoom, pan, hover
- Responsive
- Good React integration

### Backend: FastAPI
- Async support
- Auto docs (Swagger/OpenAPI)
- Pydantic validation
- High performance

### Database: Supabase
- PostgreSQL reliability
- RLS for security
- Real-time capabilities (future)
- Easy integration

## Performance Considerations

### Frontend
- React Query caching: 5 minute stale time
- Code splitting potential
- Lazy loading for charts
- Memoization for expensive computations

### Backend
- yfinance data caching (5 minute TTL)
- Model persistence to avoid retraining
- Feature computation optimization
- Connection pooling for Supabase

## Security Considerations

- RLS on all tables
- User-scoped data access
- Environment variables for secrets
- No client-side secret exposure
- CORS configuration
