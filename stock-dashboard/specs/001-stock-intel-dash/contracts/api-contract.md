# API Contract: Stock Intelligence Backend

This document defines the interface between the React Frontend and the Python Backend.

## Base URL
`http://localhost:8000/api/v1`

## Endpoints

### 1. GET `/stock/{ticker}`
Fetches combined historical data, metadata, and predictions for a ticker.

**Query Parameters:**
- `range` (optional): `1m`, `6m`, `1y` (default), `5y`.
- `model` (optional): `linear` (default), `rf`.

**Success Response (200 OK):**
```json
{
  "ticker": "AAPL",
  "profile": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "market_cap": 2800000000000,
    "high_52w": 198.23,
    "low_52w": 124.17
  },
  "history": [
    {
      "date": "2023-06-09",
      "open": 181.50,
      "high": 182.23,
      "low": 180.63,
      "close": 180.96,
      "volume": 48874100,
      "ma7": 179.45,
      "ma21": 175.32
    }
  ],
  "prediction": {
    "model": "linear",
    "predicted_price": 182.45,
    "trend": "increase",
    "current_price": 180.96
  }
}
```

**Error Responses:**
- **404 Not Found**: `{"error": "Ticker not found"}`
- **503 Service Unavailable**: `{"error": "External data source timeout"}`

---

### 2. GET `/health`
Check backend connectivity.

**Success Response (200 OK):**
```json
{"status": "ok"}
```
