# State Management (Zustand)

## Store: `useStockStore`
The central nervous system of the frontend data.

### State Variables
- `ticker`: The active stock symbol.
- `dateRange`: The chart's time horizon (`1m`, `6m`, `1y`, `5y`).
- `model`: The active ML model (`linear`, `random_forest`).
- `stockData`: The full response from the backend.
- `watchlist`: Array of tracked symbols.
- `searchHistory`: Array of recent search items.

### Actions
- `setTicker(ticker)`: Normalizes and updates the active symbol.
- `setStockData(data)`: Populates the UI with new metrics and charts.
- `addToWatchlist(item)` / `removeFromWatchlist(id)`: Manages the collection of tracked stocks.

## Store: `useUIStore`
Manages the application's visual state.

### State Variables
- `darkMode`: Boolean for theme state.
- `language`: Current locale (e.g., `hi`, `or`, `en`).
- `isDrawerOpen`: Controls the visibility of the `AskAIDrawer`.

## Why Zustand?
1. **Zero Boilerplate:** No need for providers, actions, or complex reducers.
2. **Atomic Updates:** Components only re-render when the specific piece of state they use changes.
3. **External Access:** State can be read/written outside of React components, which is useful for utility functions.
