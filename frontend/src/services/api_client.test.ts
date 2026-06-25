import { describe, it, expect, vi, beforeEach } from 'vitest';

import { api } from './api_client';
import { useAuthStore } from '../store/auth_store';

import type { User } from '@supabase/supabase-js';

describe('API Client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
    localStorage.clear();
    vi.clearAllMocks();
    useAuthStore.setState({
      user: { id: 'test-user-id', email: 'test@example.com' } as User,
      token: 'mock-access-token',
      loading: false,
      error: null,
      isAdmin: false,
    });
  });

  it('should fetch stock data from FastAPI', async () => {
    const mockResponse = {
      ticker: 'AAPL',
      profile: {},
      history: [],
      prediction: {},
      metrics: {},
      confidence: 0.9,
    };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    } as Response);

    const data = await api.getStock('AAPL', '1y', 'linear');
    expect(data).toEqual(mockResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/stock/AAPL?range=1y&model=linear'),
      expect.any(Object)
    );
  });

  it('should fetch watchlist from FastAPI', async () => {
    const mockWatchlist = [{ id: '1', ticker: 'AAPL' }];
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockWatchlist),
    } as Response);

    const data = await api.getWatchlist();
    expect(data).toEqual(mockWatchlist);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/watchlist'), expect.any(Object));
  });

  it('should add to watchlist via FastAPI', async () => {
    const mockItem = { id: '1', ticker: 'AAPL' };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockItem),
    } as Response);

    const data = await api.addToWatchlist('AAPL', 'Apple Inc.');
    expect(data).toEqual(mockItem);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/watchlist'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          ticker: 'AAPL',
          name: 'Apple Inc.',
          company_name: 'Apple Inc.',
        }),
      })
    );
  });

  it('should remove from watchlist via FastAPI', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
    } as Response);

    await api.removeFromWatchlist('1');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/watchlist/1'),
      expect.objectContaining({
        method: 'DELETE',
      })
    );
  });

  it('should throw error when FastAPI response is not ok', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'Stock not found' }),
    } as Response);

    await expect(api.getStock('INVALID', '1y', 'linear')).rejects.toThrow('Stock not found');
  });

  it('should be defined', () => {
    expect(api).toBeDefined();
    expect(api.getWatchlist).toBeDefined();
    expect(api.getStock).toBeDefined();
  });
});
