# Data Model

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | TEXT | User email |
| created_at | TIMESTAMPTZ | Creation timestamp |

### watchlists
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| ticker | TEXT | Stock symbol |
| name | TEXT | Company name |
| created_at | TIMESTAMPTZ | Added timestamp |

### search_history
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| ticker | TEXT | Stock symbol |
| searched_at | TIMESTAMPTZ | Search timestamp |

### predictions
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| ticker | TEXT | Stock symbol |
| model | TEXT | Model used |
| predicted_price | DECIMAL | Predicted price |
| actual_price | DECIMAL | Actual price (filled later) |
| confidence | DECIMAL | Confidence score |
| created_at | TIMESTAMPTZ | Prediction timestamp |

### saved_models
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| model_name | TEXT | Model identifier |
| file_path | TEXT | Path to pickled model |
| updated_at | TIMESTAMPTZ | Last training timestamp |

## Row Level Security

All tables have RLS enabled with policies:
- SELECT: Users can only read their own data
- INSERT: Users can only insert their own data
- UPDATE: Users can only update their own data
- DELETE: Users can only delete their own data

Predictions table allows authenticated read.

## Indexes

- watchlists(user_id)
- watchlists(ticker)
- search_history(user_id)
- search_history(ticker)
- predictions(ticker)
- predictions(created_at)

## API Data Types

### StockPricePoint
```typescript
interface StockPricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma7?: number;
  ma21?: number;
}
```

### CompanyProfile
```typescript
interface CompanyProfile {
  ticker: string;
  name?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  current_price?: number;
  previous_close?: number;
  currency?: string;
  exchange?: string;
  country?: string;
  week_52_high?: number;
  week_52_low?: number;
}
```

### PredictionResult
```typescript
interface PredictionResult {
  predicted_price: number;
  trend: 'increase' | 'decrease';
  confidence: number;
  model_used: string;
}
```

### ModelMetrics
```typescript
interface ModelMetrics {
  rmse: number;
  mae: number;
  r2: number;
}
```

## Feature Engineering

Features used for ML models:
- Close price
- Volume
- MA7 (7-day moving average)
- MA21 (21-day moving average)
- Returns (percentage change)
- Lag1-5 (previous 5 days' close prices)
- Volume change
