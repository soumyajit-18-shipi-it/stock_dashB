# Research: Stock Intelligence Dashboard

This document resolves technical unknowns and provides architectural decisions for the Stock Intelligence Dashboard.

## Specification Clarifications

### Decision 1: Model Selection (FR-008)
- **Decision**: **Option A (Toggle in UI)**.
- **Rationale**: Since the target users include students and developers, providing a way to compare the "Baseline" (Linear Regression) with the "Improved" (Random Forest) model adds significant educational value and demonstrates the "Intelligence" aspect of the system.
- **Alternatives**: Option B (Automatic) was rejected because it hides the complexity that the target users might want to explore.

### Decision 2: Historical Data Range (FR-009)
- **Decision**: **Option C (User-selectable: 1M, 6M, 1Y, 5Y)**.
- **Rationale**: Different users have different contexts (e.g., day trading vs. long-term investing). Providing flexibility is standard for financial dashboards.
- **Alternatives**: Option A (1 Year default) will be the initial state on load.

### Decision 3: Prediction Features (FR-010)
- **Decision**: **Option B (Multi-feature: Price + Volume + Moving Averages)**.
- **Rationale**: Using only the closing price often results in a "lagging" prediction that simply mirrors the previous day's price. Including volume and technical indicators like 7/21-day MAs provides the model with more signal for trend detection.
- **Alternatives**: Option C (User-configurable) was rejected as too complex for an MVP.

## Technical Research

### Data Acquisition: yfinance
- **Finding**: `yfinance` is a Python library. Since the frontend is a React SPA, a backend proxy (FastAPI) is mandatory to fetch data, process it (calculate MAs, train model), and serve it as JSON.
- **Best Practice**: Use `period` and `interval` parameters effectively to minimize payload size. Cache results for frequently searched tickers to improve performance.

### Predictive Modeling: scikit-learn
- **Finding**: For next-day prediction, we need to shift the target variable (Close) by one day.
- **Approach**:
    1. Fetch `N` days of data.
    2. Feature engineering: Add `MA7`, `MA21`, `Volume_Change`.
    3. Drop NaN rows (created by MAs).
    4. X = features (excluding last row), y = Close price of next day.
    5. Train on `X, y`. Use the last available row of features to predict "Tomorrow".

### Data Visualization: Plotly vs. Chart.js
- **Decision**: **Plotly**.
- **Rationale**: Plotly has superior built-in support for financial charts (Candlesticks, OHLC) and handles large time-series datasets with better interactive performance (zoom/pan) compared to Chart.js.
- **Alternative**: Chart.js was considered for its smaller bundle size but rejected for lacking advanced financial primitives.

## Rationale for Decisions
The choices prioritize **Interactivity** and **Educational Value**, aligning with the target users (Students/Beginner Investors). The Multi-feature ML approach ensures the "Intelligence" part of the dashboard isn't just a trivial placeholder.
