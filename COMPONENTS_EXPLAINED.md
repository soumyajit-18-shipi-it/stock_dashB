# Component Analysis

## Layout Components
- **Navbar:** Sticky top bar with search, language selector, and theme toggle.
- **Dashboard:** Grid-based layout that adaptively displays charts and metrics based on `stockData` presence.

## Data Visualization
- **StockChart:** 
  - Uses `react-plotly.js`.
  - Supports Candlestick and Line modes.
  - Dynamically updates based on the selected `dateRange` (1m, 6m, 1y, 5y).
- **VolumeChart:** Displays trading volume as a bar chart synced with the main price chart.

## ML & AI Components
- **PredictionCard:** 
  - Displays the predicted price and expected trend.
  - Features a "Confidence Meter" and technical highlights (RSI, Moving Averages).
- **AskAIDrawer:**
  - A slide-out panel that provides an LLM chat interface.
  - Automatically injects the current stock's data as context for the AI.

## Utility Components
- **SearchBar:** Intelligent input with debounced search and history dropdown.
- **WatchlistPanel:** Quick-access sidebar for tracked tickers.
- **LoadingSkeleton:** Tailwind-based shimmering skeletons for better UX during data fetching.
