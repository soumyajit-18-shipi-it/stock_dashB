import { create } from 'zustand';
import type { AppState } from '../types';

export const useStockStore = create<AppState>((set) => ({
  ticker: '',
  dateRange: '1y',
  model: 'linear',
  stockData: null,
  watchlist: [],
  searchHistory: [],
  predictions: [],
  isLoading: false,
  error: null,

  setTicker: (ticker) => set({ ticker: ticker.toUpperCase() }),
  setDateRange: (dateRange) => set({ dateRange }),
  setModel: (model) => set({ model }),
  setStockData: (stockData) => set({ stockData }),
  setWatchlist: (watchlist) => set({ watchlist }),
  addToWatchlist: (item) => set((state) => ({
    watchlist: state.watchlist.some((entry) => entry.ticker === item.ticker)
      ? state.watchlist.map((entry) => entry.ticker === item.ticker ? { ...entry, ...item } : entry)
      : [...state.watchlist, item],
  })),
  removeFromWatchlist: (id) => set((state) => ({
    watchlist: state.watchlist.filter((item) => item.id !== id && item.ticker !== id),
  })),
  setSearchHistory: (searchHistory) => set({ searchHistory }),
  setPredictions: (predictions) => set({ predictions }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));

export const useStore = useStockStore;
