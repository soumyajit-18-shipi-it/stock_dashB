import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface TrendIndicatorProps {
  trend: 'increase' | 'decrease';
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ trend }) => {
  const isUp = trend === 'increase';

  return (
    <div className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
      isUp ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
    }`}>
      {isUp ? (
        <>
          <ArrowUpRight className="w-4 h-4" />
          <span>Bullish</span>
        </>
      ) : (
        <>
          <ArrowDownRight className="w-4 h-4" />
          <span>Bearish</span>
        </>
      )}
    </div>
  );
};

export default TrendIndicator;
