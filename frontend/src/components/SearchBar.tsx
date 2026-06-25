import { Search, TrendingUp } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useSearchHistory } from '../hooks/useStock';
import { useStore } from '../store/stock_store';

export function SearchBar() {
  const { setTicker, isLoading } = useStore();
  const { history, add } = useSearchHistory();
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const ticker = inputValue.trim().toUpperCase();
    if (ticker) {
      setTicker(ticker);
      add(ticker);
      setShowHistory(false);
    }
  };

  const handleHistoryClick = (symbol: string) => {
    setInputValue(symbol);
    setTicker(symbol);
    add(symbol);
    setShowHistory(false);
  };

  const quickTickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'RELIANCE.NS'];

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.toUpperCase())}
            onFocus={() => setShowHistory(true)}
            onBlur={() => setTimeout(() => setShowHistory(false), 200)}
            placeholder={t('searchPlaceholder')}
            className="w-full pl-12 pr-36 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 font-medium text-white transition-all hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-700 sm:gap-2 sm:px-4"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <TrendingUp className="h-4 w-4" />
                <span>{t('analyze')}</span>
              </>
            )}
          </button>
        </div>
      </form>

      {showHistory && history.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="p-2 text-xs text-slate-400 border-b border-slate-700">
            {t('recentSearches')}
          </div>
          {history.slice(0, 5).map((item) => (
            <button
              key={item.id}
              onClick={() => handleHistoryClick(item.ticker)}
              className="w-full px-4 py-2 text-left text-white hover:bg-slate-700 transition-colors"
            >
              {item.ticker}
            </button>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-wrap justify-center gap-2">
        <span className="text-sm text-slate-400">{t('popular')}</span>
        {quickTickers.map((symbol) => (
          <button
            key={symbol}
            onClick={() => {
              setInputValue(symbol);
              setTicker(symbol);
              add(symbol);
            }}
            className="px-3 py-1 text-sm bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-full transition-colors"
          >
            {symbol}
          </button>
        ))}
      </div>
    </div>
  );
}
