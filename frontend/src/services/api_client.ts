import type { DateRange, ModelType, StockResponse, WatchlistItem, SearchHistoryItem, PredictionRecord } from '../types';

const FASTAPI_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  async getStock(ticker: string, range: DateRange, model: ModelType): Promise<StockResponse> {
    const response = await fetch(`${FASTAPI_URL}/stock/${ticker}?range=${range}&model=${model}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch stock data');
    }

    return await response.json() as StockResponse;
  },

  async getWatchlist(): Promise<WatchlistItem[]> {
    const response = await fetch(`${FASTAPI_URL}/watchlist`);
    if (!response.ok) {
      throw new Error('Failed to fetch watchlist');
    }
    return await response.json();
  },

  async addToWatchlist(ticker: string, name?: string): Promise<WatchlistItem> {
    const response = await fetch(`${FASTAPI_URL}/watchlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ticker, name }),
    });

    if (!response.ok) {
      throw new Error('Failed to add to watchlist');
    }
    return await response.json();
  },

  async removeFromWatchlist(id: string): Promise<void> {
    const response = await fetch(`${FASTAPI_URL}/watchlist/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to remove from watchlist');
    }
  },

  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    const response = await fetch(`${FASTAPI_URL}/history`);
    if (!response.ok) {
      throw new Error('Failed to fetch search history');
    }
    return await response.json();
  },

  async addSearchHistory(ticker: string): Promise<SearchHistoryItem> {
    // Note: Backend getStock already adds to history.
    // Returning a local representation for UI consistency.
    return { ticker, searched_at: new Date().toISOString() } as SearchHistoryItem;
  },

  async clearSearchHistory(): Promise<void> {
    const response = await fetch(`${FASTAPI_URL}/history`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to clear search history');
    }
  },

  async getPredictions(ticker?: string): Promise<PredictionRecord[]> {
    const url = ticker 
      ? `${FASTAPI_URL}/predictions?ticker=${ticker}` 
      : `${FASTAPI_URL}/predictions`;
      
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch predictions');
    }
    return await response.json();
  },

  async savePrediction(prediction: PredictionRecord): Promise<PredictionRecord> {
    const response = await fetch(`${FASTAPI_URL}/predictions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(prediction),
    });

    if (!response.ok) {
      throw new Error('Failed to save prediction');
    }
    return await response.json();
  },

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await fetch(`${FASTAPI_URL}/health`);
      if (response.ok) return await response.json();
      return { status: 'error' };
    } catch {
      return { status: 'down' };
    }
  },
};
