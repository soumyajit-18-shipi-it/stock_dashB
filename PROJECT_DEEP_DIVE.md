# Project Deep Dive: Reverse Engineering Report

## Summary
The **Stock Intelligence Dashboard** is a professional-grade fintech application that bridges the gap between raw market data and actionable insights. By combining traditional technical analysis (indicators) with modern ML (Ensemble regression) and generative AI (streaming chat), it provides a holistic view of stock performance.

## Design Philosophy
1. **Accuracy over Speed:** Models are retrained based on market sessions (NSE/BSE) to ensure predictions reflect the latest available close data.
2. **Resilience:** The frontend implements local-first persistence (localStorage) as a fallback if the backend or database is unreachable.
3. **Observability:** Every request is logged with latency and status code, and dedicated debug endpoints (`/debug/metrics`) expose the inner state of the data pipeline.

## Unique Features
- **Deterministic Ensemble:** Unlike many ML apps that use "black box" models, this dashboard arbitrates between Linear and Non-linear models using an empirical confidence score.
- **Contextual AI:** The "Ask AI" feature isn't just a chatbot; it's a financial analyst that receives a structured "data dump" of the current stock's indicators to provide grounded advice.
- **Multilingual Support:** Extensive i18n coverage ensures accessibility for the Indian market, supporting Hindi and Odia natively.

## Future Potential
- **Real-time Streaming:** Replacing the polling/refresh model with WebSockets.
- **Sentiment Integration:** Scrapping news and social media sentiment as new ML features.
- **Portfolio Management:** Expanding from single-stock analysis to full portfolio tracking.
