import { describe, it, expect } from 'vitest';

import { useStore } from './stock_store';

describe('Stock Store', () => {
  it('should have initial state', () => {
    const state = useStore.getState();
    expect(state.ticker).toBe('');
    expect(state.dateRange).toBe('1y');
    expect(state.model).toBe('linear');
    expect(state.stockData).toBeNull();
    expect(state.watchlist).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should set ticker', () => {
    const { setTicker } = useStore.getState();
    setTicker('AAPL');
    expect(useStore.getState().ticker).toBe('AAPL');
  });

  it('should set date range', () => {
    const { setDateRange } = useStore.getState();
    setDateRange('6m');
    expect(useStore.getState().dateRange).toBe('6m');
  });

  it('should set model', () => {
    const { setModel } = useStore.getState();
    setModel('rf');
    expect(useStore.getState().model).toBe('rf');
  });

  it('should add to watchlist', () => {
    const { addToWatchlist } = useStore.getState();
    addToWatchlist({ ticker: 'GOOGL', name: 'Alphabet Inc.' });
    expect(useStore.getState().watchlist).toHaveLength(1);
    expect(useStore.getState().watchlist[0]?.ticker).toBe('GOOGL');
  });

  it('should remove from watchlist', () => {
    const { addToWatchlist, removeFromWatchlist, setWatchlist } = useStore.getState();
    setWatchlist([]);
    addToWatchlist({ id: '1', ticker: 'MSFT' });
    addToWatchlist({ id: '2', ticker: 'NVDA' });
    removeFromWatchlist('1');
    expect(useStore.getState().watchlist).toHaveLength(1);
    expect(useStore.getState().watchlist[0]?.ticker).toBe('NVDA');
  });

  it('should set loading state', () => {
    const { setLoading } = useStore.getState();
    setLoading(true);
    expect(useStore.getState().isLoading).toBe(true);
  });

  it('should set error state', () => {
    const { setError } = useStore.getState();
    setError('Test error');
    expect(useStore.getState().error).toBe('Test error');
  });
});
