import { useStore } from '../store/stock_store';
import type { DateRange } from '../types';

const RANGES: { value: DateRange; label: string }[] = [
  { value: '1m', label: '1M' },
  { value: '6m', label: '6M' },
  { value: '1y', label: '1Y' },
  { value: '5y', label: '5Y' },
];

export function DateRangeSelector() {
  const { dateRange, setDateRange } = useStore();

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-400 mr-2">Range:</span>
      <div className="flex bg-slate-800 rounded-lg p-1">
        {RANGES.map((range) => (
          <button
            key={range.value}
            onClick={() => setDateRange(range.value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              dateRange === range.value
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {range.label}
          </button>
        ))}
      </div>
    </div>
  );
}
