# Quickstart: Validating Stock Intelligence Dashboard

This guide describes how to validate that the Stock Intelligence Dashboard is working as expected.

## Prerequisites

- **Python 3.11+**: For the backend processing and ML.
- **Node.js 20+**: For the React frontend development.
- **Internet Connection**: Required for `yfinance` to fetch live data.

## Setup & Run

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python src/main.py
   ```
2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Validation Scenarios

### Scenario 1: Basic Search & Visualization
1. Open the dashboard in a browser.
2. Enter "AAPL" in the ticker input.
3. Click "Analyze".
4. **Expected**:
    - Line chart displays 1 year of closing prices.
    - Volume chart displays trading activity.
    - Company metadata (Apple Inc.) is visible.
    - 7-day and 21-day Moving Averages are overlaid on the price chart.

### Scenario 2: Model Comparison
1. After data is loaded for "AAPL", locate the "Model Toggle".
2. Switch from "Linear Regression" to "Random Forest".
3. **Expected**:
    - The "Predicted Price" and "Trend Direction" values update (may slightly differ between models).
    - The UI indicates which model is currently active.

### Scenario 3: Data Range Selection
1. Select "1 Month" from the data range dropdown.
2. **Expected**:
    - The chart zooms in to show only the last 30 days of data.
    - Metadata and predictions remain relevant to the current search.

### Scenario 4: Error Handling
1. Enter an invalid ticker like "XYZ_INVALID_123".
2. Click "Analyze".
3. **Expected**:
    - A clear error message "Stock ticker not found" appears.
    - No broken charts are displayed.
