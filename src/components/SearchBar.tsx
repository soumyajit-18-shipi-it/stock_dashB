import { useState } from 'react';
import { Search, TrendingUp } from 'lucide-react';
import { useStore } from '../store/stock_store';
import { useSearchHistory } from '../hooks/useStock';

export function SearchBar() {
  const { setTicker, isLoading } = useStore();
  const { history } = useSearchHistory();
  const [inputValue, setInputValue] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setTicker(inputValue.trim().toUpperCase());
      setShowHistory(false);
    }
  };

  const handleHistoryClick = (symbol: string) => {
    setInputValue(symbol);
    setTicker(symbol);
    setShowHistory(false);
  };

  const quickTickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'TCS.NS'];

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
            placeholder="Enter ticker symbol (e.g., AAPL, TCS.NS)"
            className="w-full pl-12 pr-24 py-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all flex items-center gap-2"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <TrendingUp className="h-4 w-4" />
                <span>Analyze</span>
              </>
            )}
          </button>
        </div>
      </form>

      {showHistory && history.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="p-2 text-xs text-slate-400 border-b border-slate-700">Recent Searches</div>
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
        <span className="text-sm text-slate-400">Popular:</span>
        {quickTickers.map((symbol) => (
          <button
            key={symbol}
            onClick={() => {
              setInputValue(symbol);
              setTicker(symbol);
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
