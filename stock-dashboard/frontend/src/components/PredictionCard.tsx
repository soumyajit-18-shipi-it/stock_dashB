import React from 'react';
import { TrendingUp, HelpCircle } from 'lucide-react';
import { useStock } from '../store/stock_store';
import ModelToggle from './ModelToggle';
import TrendIndicator from './TrendIndicator';

const PredictionCard: React.FC = () => {
  const { stockData } = useStock();

  if (!stockData) return null;

  const { prediction } = stockData;
  const isUp = prediction.trend === 'increase';

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <h3 className="font-bold text-gray-800">ML Prediction</h3>
        </div>
        <ModelToggle />
      </div>

      <div className="space-y-6">
        <div className="text-center py-4 bg-gray-50 rounded-lg border border-dashed border-gray-200">
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Next-Day Forecast</p>
          <div className={`text-4xl font-black mb-2 ${isUp ? 'text-green-600' : 'text-red-600'}`}>
            ${prediction.predicted_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="flex justify-center">
            <TrendIndicator trend={prediction.trend as 'increase' | 'decrease'} />
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Current Price</span>
            <span className="font-semibold text-gray-700">${prediction.current_price.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Active Model</span>
            <span className="font-semibold text-blue-600">{prediction.model}</span>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-50">
          <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
            <HelpCircle className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-[11px] text-blue-600 leading-relaxed">
              Predictions are based on historical OHLCV data and technical indicators. Past performance is not indicative of future results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionCard;
