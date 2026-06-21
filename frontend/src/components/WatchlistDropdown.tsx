import { useQueries } from '@tanstack/react-query';
import { ChevronDown, Plus, Search, Star, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useSearchHistory, useWatchlist } from '../hooks/useStock';
import { api } from '../services/api_client';
import { useStore } from '../store/stock_store';

function Sparkline({ values }: { values: number[] }) {
  const points = values.length ? values : [0, 0];
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const path = points
    .map((value, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 80;
      const y = 24 - ((value - min) / range) * 24;
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg viewBox="0 0 80 24" className="h-6 w-20 text-emerald-400" aria-hidden="true">
      <path d={path} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export function WatchlistDropdown() {
  const { t } = useTranslation();
  const { ticker, setTicker } = useStore();
  const { watchlist, isLoading, add, remove } = useWatchlist();
  const { history, add: addHistory } = useSearchHistory();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  const quotes = useQueries({
    queries: watchlist.slice(0, 8).map((item) => ({
      queryKey: ['watchlist-stock', item.ticker],
      queryFn: () => api.getStock(item.ticker, '1m', 'linear'),
      staleTime: 60_000,
      retry: 0,
      enabled: open,
    })),
  });

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const quoteMap = useMemo(() => {
    const map = new Map<string, (typeof quotes)[number]['data']>();
    watchlist.slice(0, 8).forEach((item, index) => map.set(item.ticker, quotes[index]?.data));
    return map;
  }, [quotes, watchlist]);

  const filteredWatchlist = useMemo(() => {
    const term = search.trim().toUpperCase();
    if (!term) return watchlist;
    return watchlist.filter(
      (item) => item.ticker.includes(term) || (item.name || '').toUpperCase().includes(term)
    );
  }, [search, watchlist]);

  const handleSelect = (symbol: string) => {
    setTicker(symbol);
    void addHistory(symbol);
    setOpen(false);
  };

  const handleAdd = async () => {
    const symbol = search.trim().toUpperCase();
    if (!symbol) return;
    await add(symbol);
    setTicker(symbol);
    void addHistory(symbol);
    setSearch('');
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-2 rounded-lg bg-slate-700 px-3 py-1.5 text-sm text-white transition-colors hover:bg-slate-600"
        aria-expanded={open}
      >
        <Star className="h-4 w-4 text-yellow-400" />
        {t('watchlistMenu')}
        <ChevronDown className="h-4 w-4" />
      </button>

      {open && (
        <div className="fixed inset-0 z-[80] overflow-y-auto border-slate-700 bg-slate-900 p-4 shadow-2xl sm:absolute sm:inset-auto sm:right-0 sm:top-full sm:mt-2 sm:w-[28rem] sm:rounded-xl sm:border">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
              <Star className="h-5 w-5 text-yellow-400" />
              {t('watchlistMenu')}
            </h3>
            <button
              className="rounded-lg px-2 py-1 text-sm text-slate-400 hover:bg-slate-800 hover:text-white sm:hidden"
              onClick={() => setOpen(false)}
            >
              {t('cancel')}
            </button>
          </div>

          <div className="mb-4 flex gap-2">
            <div className="relative min-w-0 flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value.toUpperCase())}
                placeholder={t('searchTickers')}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 py-2 pl-9 pr-3 text-sm text-white placeholder-slate-500"
              />
            </div>
            <button
              onClick={handleAdd}
              className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
            >
              <Plus className="h-4 w-4" />
              {t('addTicker')}
            </button>
          </div>

          <div className="space-y-2">
            {isLoading ? (
              <div className="h-16 animate-pulse rounded-lg bg-slate-800" />
            ) : watchlist.length === 0 ? (
              <p className="rounded-lg bg-slate-800/50 p-4 text-center text-sm text-slate-400">
                {t('noStocks')}
              </p>
            ) : filteredWatchlist.length === 0 ? (
              <p className="rounded-lg bg-slate-800/50 p-4 text-center text-sm text-slate-400">
                {t('notAvailable')}
              </p>
            ) : (
              filteredWatchlist.map((item) => {
                const quote = quoteMap.get(item.ticker);
                const profile = quote?.profile;
                const price = profile?.current_price;
                const previous = profile?.previous_close;
                const change =
                  price != null && previous ? ((price - previous) / previous) * 100 : null;
                const values = quote?.history?.slice(-12).map((point) => point.close) || [];
                return (
                  <div
                    key={item.id || item.ticker}
                    className={`rounded-lg border p-3 ${ticker === item.ticker ? 'border-emerald-500/30 bg-emerald-600/10' : 'border-slate-700 bg-slate-800/50'}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <button
                        onClick={() => handleSelect(item.ticker)}
                        className="min-w-0 flex-1 text-left"
                      >
                        <p className="font-medium text-white">{item.ticker}</p>
                        <p className="truncate text-xs text-slate-400">
                          {profile?.name || item.name || t('notAvailable')}
                        </p>
                      </button>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-white">
                          {price != null ? price.toFixed(2) : '--'}
                        </p>
                        <p
                          className={`text-xs ${change == null || change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}
                        >
                          {change == null ? '--' : `${change.toFixed(2)}%`}
                        </p>
                      </div>
                      <Sparkline values={values} />
                      {item.id && (
                        <button
                          onClick={() => void remove(item.id!)}
                          className="rounded p-1 hover:bg-red-500/20"
                          aria-label={t('removeTicker')}
                        >
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="mt-4 border-t border-slate-700 pt-3">
            <h4 className="mb-2 text-sm font-medium text-white">{t('recentlyViewed')}</h4>
            <div className="flex flex-wrap gap-2">
              {history.slice(0, 6).map((item) => (
                <button
                  key={`${item.ticker}-${item.searched_at || item.id}`}
                  onClick={() => handleSelect(item.ticker)}
                  className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-slate-700"
                >
                  {item.ticker}
                </button>
              ))}
              {history.length === 0 && (
                <p className="text-xs text-slate-400">{t('notAvailable')}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
