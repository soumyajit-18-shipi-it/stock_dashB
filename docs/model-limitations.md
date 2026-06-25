# Model Limitations

## Stock Prediction

- Uses OHLCV-derived technical features, not complete fundamental, macroeconomic, options, order-book, or news data.
- Predicts one-day-ahead closing price, which can be invalidated by earnings, policy changes, market shocks, or liquidity events.
- Metrics are based on historical train/test splits and can degrade in live markets.
- Confidence is a heuristic combining R2 and relative RMSE; it is not a probability of profit.

## Indic Intent Classifier

- Small sample dataset.
- Intended as prompt-routing support only.
- May fail on spelling variation, code-mixing, dialectal language, speech transcripts, or unsupported languages.

## LLM Features

- Hosted LLMs can hallucinate.
- Provider model versions and behavior can change.
- The app injects stock data context, but the model may still produce inaccurate explanations.

## Data Limitations

- Yahoo Finance and Finnhub availability, delays, and rate limits can affect output.
- Some exchanges may have delayed or incomplete metadata.
