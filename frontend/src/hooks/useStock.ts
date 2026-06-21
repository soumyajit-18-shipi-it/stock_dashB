import { useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '../services/api_client';
import { useStore } from '../store/stock_store';

export function useStock() {
  const { ticker, dateRange, model, setLoading, setError, setStockData } = useStore();

  const query = useQuery({
    queryKey: ['stock', ticker, dateRange, model],
    queryFn: async () => {
      if (!ticker) return null;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getStock(ticker, dateRange, model);
        setStockData(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch stock data';
        setError(message);
        setStockData(null);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return query;
}

export function useWatchlist() {
  const { addToWatchlist, removeFromWatchlist } = useStore();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: api.getWatchlist,
  });

  const watchlist = data || [];

  const add = async (ticker: string, name?: string) => {
    const symbol = ticker.trim().toUpperCase();
    if (!symbol) throw new Error('Ticker is required');
    const optimistic = { id: symbol, ticker: symbol, name };
    queryClient.setQueryData(['watchlist'], (current: unknown) => {
      const items = Array.isArray(current) ? (current as typeof watchlist) : [];
      return items.some((entry) => entry.ticker === symbol) ? items : [...items, optimistic];
    });
    addToWatchlist(optimistic);
    const item = await api.addToWatchlist(symbol, name);
    queryClient.setQueryData(['watchlist'], (current: unknown) => {
      const items = Array.isArray(current) ? (current as typeof watchlist) : [];
      return items.map((entry) => (entry.ticker === symbol ? item : entry));
    });
    return item;
  };

  const remove = async (id: string) => {
    removeFromWatchlist(id);
    queryClient.setQueryData(['watchlist'], (current: unknown) => {
      const items = Array.isArray(current) ? (current as typeof watchlist) : [];
      return items.filter((entry) => entry.id !== id && entry.ticker !== id);
    });
    await api.removeFromWatchlist(id);
  };

  return { watchlist, isLoading, add, remove };
}

export function useSearchHistory() {
  const { setSearchHistory } = useStore();
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: api.getSearchHistory,
  });

  const history = data || [];

  const add = async (ticker: string) => {
    try {
      const item = await api.addSearchHistory(ticker);
      queryClient.setQueryData(['searchHistory'], (current: unknown) => {
        const items = Array.isArray(current) ? (current as typeof history) : [];
        return [item, ...items.filter((entry) => entry.ticker !== item.ticker)].slice(0, 20);
      });
      void refetch();
    } catch (err) {
      console.error('Failed to add to search history:', err);
    }
  };

  const clear = async () => {
    await api.clearSearchHistory();
    setSearchHistory([]);
    refetch();
  };

  return { history, isLoading, add, clear };
}

export function usePredictions(ticker?: string) {
  const { data, isLoading } = useQuery({
    queryKey: ['predictions', ticker],
    queryFn: () => api.getPredictions(ticker),
  });

  const predictions = data || [];

  return { predictions, isLoading };
}
