# Machine Learning in Stock Intelligence Dashboard

## Problem Statement
The goal is to predict the next day's closing price for a given stock ticker based on its historical performance and technical indicators.

## Models Used

### 1. Linear Regression
- **Purpose:** Captures the linear trend and momentum of the stock.
<<<<<<< HEAD
- **Implementation:** LinearRegression from sklearn.linear_model.
- **Scaling:** Uses StandardScaler to handle varying feature magnitudes (e.g., Volume vs. RSI).
=======
- **Implementation:** `LinearRegression` from `sklearn.linear_model`.
- **Scaling:** Uses `StandardScaler` to handle varying feature magnitudes (e.g., Volume vs. RSI).
>>>>>>> 43c89386f948b8a790430e72f627b7b9a714bb65

### 2. Random Forest Regressor
- **Purpose:** Captures non-linear relationships and complex interactions between indicators.
- **Configuration:** 200 trees, max depth of 8, minimum 5 samples per leaf.
- **Advantage:** Robust to outliers and identifies feature importance.

## Feature Engineering
<<<<<<< HEAD
The FeatureEngineer class calculates the following:
- **Moving Averages:** 7-day and 21-day windows.
- **Returns:** Percentage change in daily closing prices.
- **Lag Features:** Previous 5 days' closing prices (lag1 to lag5).
- **Volume Change:** Percentage change in trading volume.
- **RSI:** Relative Strength Index (via TechnicalIndicators).
=======
The `FeatureEngineer` class calculates the following:
- **Moving Averages:** 7-day and 21-day windows.
- **Returns:** Percentage change in daily closing prices.
- **Lag Features:** Previous 5 days' closing prices (`lag1` to `lag5`).
- **Volume Change:** Percentage change in trading volume.
- **RSI:** Relative Strength Index (via `TechnicalIndicators`).
>>>>>>> 43c89386f948b8a790430e72f627b7b9a714bb65

## Prediction Pipeline
1. **Data Fetching:** OHLCV data for the requested range (default 1y).
2. **Preprocessing:** Feature calculation and handling of missing values (dropping NaNs).
3. **Training/Inference:**
<<<<<<< HEAD
   - Checks if a serialized .pkl model exists and is fresh (within current market session).
   - If stale, retrains on the updated dataset.
   - Executes both models in the Ensemble.
4. **Arbitration:**
   - Compares confidence scores (blended R² and RMSE penalty).
=======
   - Checks if a serialized `.pkl` model exists and is fresh (within current market session).
   - If stale, retrains on the updated dataset.
   - Executes both models in the Ensemble.
4. **Arbitration:**
   - Compares confidence scores (blended RÂ² and RMSE penalty).
>>>>>>> 43c89386f948b8a790430e72f627b7b9a714bb65
   - Picks the more reliable prediction or blends them if they are within a tight threshold.

## Confidence Scoring
Confidence is calculated as:
<<<<<<< HEAD
score = ((r2 + 1) / 2) * (1 - min(rmse / mean_price, 0.5))
This ensures that models with high relative error are penalized even if their R² is high.
=======
`score = ((r2 + 1) / 2) * (1 - min(rmse / mean_price, 0.5))`
This ensures that models with high relative error are penalized even if their RÂ² is high.
>>>>>>> 43c89386f948b8a790430e72f627b7b9a714bb65
