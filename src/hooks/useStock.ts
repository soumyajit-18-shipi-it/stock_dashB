import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api_client';
import { useStore } from '../store/stock_store';

export function useStock() {
  const { ticker, dateRange, model, setLoading, setError } = useStore();

  const query = useQuery({
    queryKey: ['stock', ticker, dateRange, model],
    queryFn: async () => {
      if (!ticker) return null;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getStock(ticker, dateRange, model);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch stock data';
        setError(message);
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

  const { data, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: api.getWatchlist,
  });

  const watchlist = data || [];

  const add = async (ticker: string, name?: string) => {
    const item = await api.addToWatchlist(ticker, name);
    addToWatchlist(item);
    return item;
  };

  const remove = async (id: string) => {
    await api.removeFromWatchlist(id);
    removeFromWatchlist(id);
  };

  return { watchlist, isLoading, add, remove };
}

export function useSearchHistory() {
  const { setSearchHistory } = useStore();

  const { data, isLoading } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: api.getSearchHistory,
  });

  const history = data || [];

  const clear = async () => {
    await api.clearSearchHistory();
    setSearchHistory([]);
  };

  return { history, isLoading, clear };
}

export function usePredictions(ticker?: string) {
  const { data, isLoading } = useQuery({
    queryKey: ['predictions', ticker],
    queryFn: () => api.getPredictions(ticker),
  });

  const predictions = data || [];

  return { predictions, isLoading };
}
