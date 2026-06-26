import { useAuthStore } from '../store/auth_store';

import type {
  DateRange,
  ModelType,
  StockResponse,
  WatchlistItem,
  SearchHistoryItem,
  PredictionRecord,
  FeedbackIssue,
  AdminStats,
} from '../types';

const VITE_API_URL = import.meta.env.VITE_API_URL;
const hasExplicitApiUrl = Boolean(VITE_API_URL && VITE_API_URL !== '/api/v1');
const FASTAPI_URL =
  hasExplicitApiUrl
    ? VITE_API_URL
    : typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';
const WATCHLIST_KEY = 'stock_watchlist';
const HISTORY_KEY = 'stock_search_history';

function normalizeTicker(ticker: string) {
  return ticker.trim().toUpperCase();
}

if (!hasExplicitApiUrl && import.meta.env.DEV) {
  console.warn(
    'VITE_API_URL is not set. Using local backend fallback http://localhost:8000/api/v1.'
  );
}

function userScopedKey(key: string) {
  const userId = useAuthStore.getState().user?.id;
  return `${key}:${userId || 'anonymous'}`;
}

function readLocalArray<T>(key: string): T[] {
  try {
    const value = localStorage.getItem(key);
    return value ? (JSON.parse(value) as T[]) : [];
  } catch {
    return [];
  }
}

function writeLocalArray<T>(key: string, value: T[]) {
  localStorage.setItem(key, JSON.stringify(value));
}

function readLocalWatchlist() {
  return readLocalArray<WatchlistItem>(userScopedKey(WATCHLIST_KEY));
}

function writeLocalWatchlist(items: WatchlistItem[]) {
  const deduped = items.reduce<WatchlistItem[]>((acc, item) => {
    const ticker = normalizeTicker(item.ticker);
    if (!ticker || acc.some((entry) => entry.ticker === ticker)) return acc;
    acc.push({ ...item, ticker, id: item.id || ticker });
    return acc;
  }, []);
  writeLocalArray(userScopedKey(WATCHLIST_KEY), deduped);
  return deduped;
}

function readLocalHistory() {
  return readLocalArray<SearchHistoryItem>(userScopedKey(HISTORY_KEY));
}

function writeLocalHistory(items: SearchHistoryItem[]) {
  const deduped = items.reduce<SearchHistoryItem[]>((acc, item) => {
    const ticker = normalizeTicker(item.ticker);
    if (!ticker) return acc;
    if (acc.some((entry) => entry.ticker === ticker)) return acc;
    return [...acc, { ...item, ticker, id: item.id || ticker }];
  }, []);
  writeLocalArray(userScopedKey(HISTORY_KEY), deduped.slice(0, 20));
  return deduped.slice(0, 20);
}

function requireAuthToken() {
  const token = useAuthStore.getState().token;
  if (!token) {
    throw new Error('Please sign in with Google to use this feature.');
  }
  return token;
}

function isAuthError(error: unknown) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    message.includes('sign in') ||
    message.includes('401') ||
    message.includes('403') ||
    message.toLowerCase().includes('unauthorized') ||
    message.toLowerCase().includes('forbidden')
  );
}

async function parseApiError(response: Response, fallback: string) {
  try {
    const errorData = await response.json();
    return errorData.detail || errorData.message || fallback;
  } catch {
    return `${fallback} (${response.status})`;
  }
}

async function fetchWithAuth(
  url: string,
  options: RequestInit = {},
  authOptions: { requireAuth?: boolean } = {}
): Promise<Response> {
  const token = useAuthStore.getState().token;
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  if (authOptions.requireAuth) {
    headers.set('Authorization', `Bearer ${requireAuthToken()}`);
  } else if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (import.meta.env.DEV) {
    console.info('API auth debug: token present:', token ? 'yes' : 'no');
  }

  return fetch(url, {
    ...options,
    headers,
  });
}

export const api = {
  async getStock(ticker: string, range: DateRange, model: ModelType): Promise<StockResponse> {
    const response = await fetchWithAuth(`${FASTAPI_URL}/stock/${ticker}?range=${range}&model=${model}`);

    if (!response.ok) {
      let errorMessage = 'Failed to fetch stock data';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = `Server responded with status ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    return (await response.json()) as StockResponse;
  },

  async getWatchlist(): Promise<WatchlistItem[]> {
    try {
      const response = await fetchWithAuth(
        `${FASTAPI_URL}/watchlist`,
        {},
        { requireAuth: true }
      );
      if (!response.ok) {
        throw new Error(await parseApiError(response, 'Failed to fetch watchlist'));
      }
      const items = (await response.json()) as WatchlistItem[];
      return writeLocalWatchlist(items);
    } catch (error) {
      if (isAuthError(error)) throw error;
      return readLocalWatchlist();
    }
  },

  async addToWatchlist(ticker: string, name?: string): Promise<WatchlistItem> {
    requireAuthToken();
    const symbol = normalizeTicker(ticker);
    const existing = readLocalWatchlist().find((item) => item.ticker === symbol);
    if (existing) return existing;

    const localItem: WatchlistItem = {
      id: symbol,
      ticker: symbol,
      name,
      created_at: new Date().toISOString(),
    };
    writeLocalWatchlist([...readLocalWatchlist(), localItem]);

    try {
      const response = await fetchWithAuth(`${FASTAPI_URL}/watchlist`, {
        method: 'POST',
        body: JSON.stringify({ ticker: symbol, name, company_name: name }),
      }, { requireAuth: true });

      if (!response.ok) {
        throw new Error(await parseApiError(response, 'Failed to add to watchlist'));
      }
      const item = (await response.json()) as WatchlistItem;
      writeLocalWatchlist([
        ...readLocalWatchlist().filter((entry) => entry.ticker !== symbol),
        { ...item, ticker: normalizeTicker(item.ticker || symbol) },
      ]);
      return item;
    } catch (error) {
      if (isAuthError(error)) {
        writeLocalWatchlist(readLocalWatchlist().filter((entry) => entry.ticker !== symbol));
        throw error;
      }
      return localItem;
    }
  },

  async removeFromWatchlist(id: string): Promise<void> {
    requireAuthToken();
    const current = readLocalWatchlist();
    const target = current.find((item) => item.id === id || item.ticker === normalizeTicker(id));
    writeLocalWatchlist(
      current.filter((item) => item.id !== id && item.ticker !== normalizeTicker(id))
    );

    try {
      const response = await fetchWithAuth(`${FASTAPI_URL}/watchlist/${target?.id || id}`, {
        method: 'DELETE',
      }, { requireAuth: true });

      if (!response.ok) {
        throw new Error(await parseApiError(response, 'Failed to remove from watchlist'));
      }
    } catch (error) {
      if (isAuthError(error)) throw error;
      // Local persistence has already been updated.
    }
  },

  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    try {
      const response = await fetchWithAuth(
        `${FASTAPI_URL}/history`,
        {},
        { requireAuth: true }
      );
      if (!response.ok) {
        throw new Error(await parseApiError(response, 'Failed to fetch search history'));
      }
      const items = (await response.json()) as SearchHistoryItem[];
      const local = readLocalHistory();
      return writeLocalHistory([...local, ...items]);
    } catch (error) {
      if (isAuthError(error)) throw error;
      return readLocalHistory();
    }
  },

  async addSearchHistory(ticker: string): Promise<SearchHistoryItem> {
    requireAuthToken();
    const item = {
      id: normalizeTicker(ticker),
      query: normalizeTicker(ticker),
      ticker: normalizeTicker(ticker),
      searched_at: new Date().toISOString(),
    } as SearchHistoryItem;
    writeLocalHistory([item, ...readLocalHistory()]);
    try {
      const response = await fetchWithAuth(`${FASTAPI_URL}/history`, {
        method: 'POST',
        body: JSON.stringify({ query: item.query || item.ticker, ticker: item.ticker }),
      }, { requireAuth: true });
      if (!response.ok) {
        throw new Error(await parseApiError(response, 'Failed to save search history'));
      }
      const saved = (await response.json()) as SearchHistoryItem;
      writeLocalHistory([saved, ...readLocalHistory()]);
      return saved;
    } catch (error) {
      if (isAuthError(error)) {
        writeLocalHistory(readLocalHistory().filter((entry) => entry.id !== item.id));
        throw error;
      }
      return item;
    }
  },

  async clearSearchHistory(): Promise<void> {
    requireAuthToken();
    const previousHistory = readLocalHistory();
    writeLocalHistory([]);
    try {
      const response = await fetchWithAuth(`${FASTAPI_URL}/history`, {
        method: 'DELETE',
      }, { requireAuth: true });

      if (!response.ok) {
        writeLocalHistory(previousHistory);
        throw new Error(await parseApiError(response, 'Failed to clear search history'));
      }
    } catch (error) {
      if (isAuthError(error)) {
        writeLocalHistory(previousHistory);
        throw error;
      }
      // Non-auth error: local is already cleared, server may be unavailable.
    }
  },

  async getPredictions(ticker?: string): Promise<PredictionRecord[]> {
    const url = ticker
      ? `${FASTAPI_URL}/predictions?ticker=${ticker}`
      : `${FASTAPI_URL}/predictions`;

    const response = await fetchWithAuth(url, {}, { requireAuth: true });
    if (!response.ok) {
      throw new Error(await parseApiError(response, 'Failed to fetch predictions'));
    }
    return await response.json();
  },

  async savePrediction(prediction: PredictionRecord): Promise<PredictionRecord> {
    const response = await fetchWithAuth(`${FASTAPI_URL}/predictions`, {
      method: 'POST',
      body: JSON.stringify(prediction),
    }, { requireAuth: true });

    if (!response.ok) {
      throw new Error(await parseApiError(response, 'Failed to save prediction'));
    }
    return await response.json();
  },

  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await fetchWithAuth(`${FASTAPI_URL}/health`);
      if (response.ok) return await response.json();
      return { status: 'error' };
    } catch {
      return { status: 'down' };
    }
  },

  async syncProfile(): Promise<{ success: boolean }> {
    const response = await fetchWithAuth(
      `${FASTAPI_URL}/auth/sync-profile`,
      { method: 'POST' },
      { requireAuth: true }
    );
    if (!response.ok) {
      throw new Error(await parseApiError(response, 'Failed to sync user profile'));
    }
    return (await response.json()) as { success: boolean };
  },

  // Feedback API Endpoints
  async submitFeedback(
    category: string,
    title: string,
    description: string,
    pageUrl?: string,
    screenshotUrl?: string
  ): Promise<FeedbackIssue> {
    const response = await fetchWithAuth(`${FASTAPI_URL}/feedback`, {
      method: 'POST',
      body: JSON.stringify({
        category,
        title,
        description,
        page_url: pageUrl,
        screenshot_url: screenshotUrl,
      }),
    }, { requireAuth: true });

    if (!response.ok) {
      let msg = 'Failed to submit feedback';
      try {
        const err = await response.json();
        msg = err.detail || err.message || msg;
      } catch (e) {
        console.warn('Failed to parse error response JSON:', e);
      }
      throw new Error(msg);
    }
    return (await response.json()) as FeedbackIssue;
  },

  async getMyFeedback(): Promise<FeedbackIssue[]> {
    const response = await fetchWithAuth(
      `${FASTAPI_URL}/feedback/my`,
      {},
      { requireAuth: true }
    );
    if (!response.ok) {
      throw new Error('Failed to fetch user feedback');
    }
    return (await response.json()) as FeedbackIssue[];
  },

  // Admin API Endpoints
  async getAdminStats(): Promise<AdminStats> {
    const response = await fetchWithAuth(
      `${FASTAPI_URL}/admin/stats`,
      {},
      { requireAuth: true }
    );
    if (!response.ok) {
      let msg = 'Failed to fetch admin statistics';
      try {
        const err = await response.json();
        msg = err.detail || err.message || msg;
      } catch (e) {
        console.warn('Failed to parse error response JSON:', e);
      }
      throw new Error(msg);
    }
    return (await response.json()) as AdminStats;
  },

  async getAdminFeedback(status?: string, category?: string, priority?: string): Promise<FeedbackIssue[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    if (priority) params.append('priority', priority);
    
    const queryString = params.toString();
    const url = queryString ? `${FASTAPI_URL}/admin/feedback?${queryString}` : `${FASTAPI_URL}/admin/feedback`;
    
    const response = await fetchWithAuth(url, {}, { requireAuth: true });
    if (!response.ok) {
      let msg = 'Failed to fetch all feedback';
      try {
        const err = await response.json();
        msg = err.detail || err.message || msg;
      } catch (e) {
        console.warn('Failed to parse error response JSON:', e);
      }
      throw new Error(msg);
    }
    return (await response.json()) as FeedbackIssue[];
  },
};
