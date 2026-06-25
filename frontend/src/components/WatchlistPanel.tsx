import { Star, Trash2, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { useWatchlist } from '../hooks/useStock';
import { useStore } from '../store/stock_store';

export function WatchlistPanel() {
  const { watchlist, isLoading, remove } = useWatchlist();
  const { ticker, setTicker } = useStore();
  const { t } = useTranslation();

  const handleRemove = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await remove(id);
  };

  const handleSelect = (symbol: string) => {
    setTicker(symbol);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Star className="h-5 w-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">{t('watchlist')}</h3>
        </div>
        <span className="text-sm text-slate-400">
          {t('stocksCount', { count: watchlist.length })}
        </span>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-2">
          <div className="h-10 bg-slate-700 rounded" />
          <div className="h-10 bg-slate-700 rounded" />
        </div>
      ) : watchlist.length === 0 ? (
        <p className="text-slate-400 text-sm text-center py-4">{t('noStocks')}</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {watchlist.map((item) => (
            <div
              key={item.id}
              onClick={() => handleSelect(item.ticker)}
              className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                ticker === item.ticker
                  ? 'bg-emerald-600/20 border border-emerald-500/30'
                  : 'bg-slate-700/50 hover:bg-slate-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <div>
                  <p className="text-white font-medium">{item.ticker}</p>
                  {item.name && <p className="text-xs text-slate-400">{item.name}</p>}
                </div>
              </div>
              <button
                onClick={(e) => handleRemove(item.id!, e)}
                className="p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <Trash2 className="h-4 w-4 text-red-400" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
