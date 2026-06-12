# API Contract

## Base URL
`/api/v1`

## Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Get Stock Data

```
GET /stock/{ticker}
```

**Parameters:**
- `ticker` (path): Stock symbol (e.g., AAPL, TCS.NS)
- `range` (query): Date range - `1m`, `6m`, `1y`, `5y` (default: `1y`)
- `model` (query): ML model - `linear`, `rf` (default: `linear`)

**Response:**
```json
{
  "ticker": "AAPL",
  "profile": {
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2800000000000,
    "current_price": 178.52,
    "previous_close": 176.85,
    "currency": "USD",
    "exchange": "NMS",
    "country": "United States",
    "week_52_high": 199.62,
    "week_52_low": 124.17
  },
  "history": [
    {
      "date": "2024-01-02",
      "open": 185.64,
      "high": 186.20,
      "low": 183.65,
      "close": 185.56,
      "volume": 48174400,
      "ma7": 184.23,
      "ma21": 182.45
    }
  ],
  "prediction": {
    "predicted_price": 186.42,
    "trend": "increase",
    "confidence": 0.78,
    "model_used": "rf"
  },
  "metrics": {
    "rmse": 2.34,
    "mae": 1.87,
    "r2": 0.85
  },
  "confidence": 0.78
}
```

**Error Response:**
```json
{
  "detail": "No data found for ticker: INVALID_TICKER"
}
```

---

### Add to Watchlist

```
POST /watchlist
```

**Request Body:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc."
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Get Watchlist

```
GET /watchlist
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Remove from Watchlist

```
DELETE /watchlist/{id}
```

**Response:**
```json
{
  "status": "deleted"
}
```

---

### Get Search History

```
GET /history
```

**Response:**
```json
[
  {
    "id": "uuid-here",
    "ticker": "AAPL",
    "searched_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Clear Search History

```
DELETE /history
```

**Response:**
```json
{
  "status": "cleared"
}
```

---

### Get Predictions

```
GET /predictions
```

**Query Parameters:**
- `ticker` (optional): Filter by ticker

**Response:**
```json
[
  {
    "id": "uuid-here",
    "ticker": "AAPL",
    "model": "rf",
    "predicted_price": 186.42,
    "actual_price": null,
    "confidence": 0.78,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### Save Prediction

```
POST /predictions
```

**Request Body:**
```json
{
  "ticker": "AAPL",
  "model": "rf",
  "predicted_price": 186.42,
  "confidence": 0.78
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "ticker": "AAPL",
  "model": "rf",
  "predicted_price": 186.42,
  "actual_price": null,
  "confidence": 0.78,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Headers

### Request Headers
- `Content-Type: application/json`
- `X-User-Id: <user-id>` (optional, for user-scoped data)

### Response Headers
- `Content-Type: application/json`
- `Access-Control-Allow-Origin: *`

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
