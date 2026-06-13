# Frontend Architecture: Deep Dive

## Technology Stack
- **React 18:** Functional components with hooks.
- **Zustand:** Minimalist state management.
- **Tailwind CSS:** Utility-first styling with dark mode support.
- **Tanstack Query:** Robust caching and revalidation logic.

## Store Structure (`src/store/`)
- `useStockStore`: Manages `ticker`, `stockData`, `watchlist`, and `predictions`.
- `useUIStore`: Manages `darkMode`, `language`, and `drawerState`.

## Key Components
- **Dashboard:** The main layout orchestrating the chart and metrics.
- **StockChart:** Plotly-based interactive candlestick and line charts.
- **PredictionCard:** Displays ML results with trend indicators and confidence gauges.
- **AskAIDrawer:** An interactive panel for context-aware AI analysis.

## Interaction Flow
1. **Search:** User triggers a search in `SearchBar`.
2. **State:** Store updates `ticker`.
3. **Query:** `useStock` hook fires, fetching data from the backend.
4. **Render:** Components reactively update when `stockData` is populated.

## Internationalization (i18n)
- Uses `react-i18next`.
- Supports 5+ languages including Hindi and Odia.
- Translation files are stored in `src/locales/`.
