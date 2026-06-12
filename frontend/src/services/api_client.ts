import type { DateRange, ModelType, StockResponse, WatchlistItem, SearchHistoryItem, PredictionRecord } from '../types';

const FASTAPI_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const WATCHLIST_KEY = 'stock_watchlist';
const HISTORY_KEY = 'stock_search_history';

function normalizeTicker(ticker: string) {
  return ticker.trim().toUpperCase();
}

function readLocalArray<T>(key: string): T[] {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) as T[] : [];
  } catch {
    return [];
  }
}

function writeLocalArray<T>(key: string, value: T[]) {
  localStorage.setItem(key, JSON.stringify(value));
}

function readLocalWatchlist() {
  return readLocalArray<WatchlistItem>(WATCHLIST_KEY);
}

function writeLocalWatchlist(items: WatchlistItem[]) {
  const deduped = items.reduce<WatchlistItem[]>((acc, item) => {
    const ticker = normalizeTicker(item.ticker);
    if (!ticker || acc.some((entry) => entry.ticker === ticker)) return acc;
    acc.push({ ...item, ticker, id: item.id || ticker });
    return acc;
  }, []);
  writeLocalArray(WATCHLIST_KEY, deduped);
  return deduped;
}

function readLocalHistory() {
  return readLocalArray<SearchHistoryItem>(HISTORY_KEY);
}

function writeLocalHistory(items: SearchHistoryItem[]) {
  const deduped = items.reduce<SearchHistoryItem[]>((acc, item) => {
    const ticker = normalizeTicker(item.ticker);
    if (!ticker) return acc;
    if (acc.some((entry) => entry.ticker === ticker)) return acc;
    return [...acc, { ...item, ticker, id: item.id || ticker }];
  }, []);
  writeLocalArray(HISTORY_KEY, deduped.slice(0, 20));
  return deduped.slice(0, 20);
}

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
    try {
      const response = await fetch(`${FASTAPI_URL}/watchlist`);
      if (!response.ok) {
        throw new Error('Failed to fetch watchlist');
      }
      const items = await response.json() as WatchlistItem[];
      return writeLocalWatchlist(items);
    } catch {
      return readLocalWatchlist();
    }
  },

  async addToWatchlist(ticker: string, name?: string): Promise<WatchlistItem> {
    const symbol = normalizeTicker(ticker);
    const existing = readLocalWatchlist().find((item) => item.ticker === symbol);
    if (existing) return existing;

    const localItem: WatchlistItem = { id: symbol, ticker: symbol, name, created_at: new Date().toISOString() };
    writeLocalWatchlist([...readLocalWatchlist(), localItem]);

    try {
      const response = await fetch(`${FASTAPI_URL}/watchlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: symbol, name }),
      });

      if (!response.ok) {
        throw new Error('Failed to add to watchlist');
      }
      const item = await response.json() as WatchlistItem;
      writeLocalWatchlist([...readLocalWatchlist().filter((entry) => entry.ticker !== symbol), { ...item, ticker: normalizeTicker(item.ticker || symbol) }]);
      return item;
    } catch {
      return localItem;
    }
  },

  async removeFromWatchlist(id: string): Promise<void> {
    const current = readLocalWatchlist();
    const target = current.find((item) => item.id === id || item.ticker === normalizeTicker(id));
    writeLocalWatchlist(current.filter((item) => item.id !== id && item.ticker !== normalizeTicker(id)));

    try {
      const response = await fetch(`${FASTAPI_URL}/watchlist/${target?.id || id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove from watchlist');
      }
    } catch {
      // Local persistence has already been updated.
    }
  },

  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    try {
      const response = await fetch(`${FASTAPI_URL}/history`);
      if (!response.ok) {
        throw new Error('Failed to fetch search history');
      }
      const items = await response.json() as SearchHistoryItem[];
      const local = readLocalHistory();
      return writeLocalHistory([...local, ...items]);
    } catch {
      return readLocalHistory();
    }
  },

  async addSearchHistory(ticker: string): Promise<SearchHistoryItem> {
    const item = { id: normalizeTicker(ticker), ticker: normalizeTicker(ticker), searched_at: new Date().toISOString() } as SearchHistoryItem;
    writeLocalHistory([item, ...readLocalHistory()]);
    return item;
  },

  async clearSearchHistory(): Promise<void> {
    writeLocalHistory([]);
    try {
      const response = await fetch(`${FASTAPI_URL}/history`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to clear search history');
      }
    } catch {
      // Local persistence has already been updated.
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
