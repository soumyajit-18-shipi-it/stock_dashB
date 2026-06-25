import { TrendingUp, TrendingDown, Brain } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { currencyForStock, formatCurrency } from '../utils/format';

import type { PredictionResult, ModelMetrics, StockResponse } from '../types';

interface PredictionCardProps {
  prediction: PredictionResult;
  metrics: ModelMetrics;
  stockData?: StockResponse;
}

export function PredictionCard({ prediction, metrics, stockData }: PredictionCardProps) {
  const { t } = useTranslation();
  const isUp = prediction.trend === 'increase';
  const confidencePercent = Math.round(prediction.confidence * 100);
  const currency = currencyForStock(stockData);

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
      <div className="flex items-center gap-3 mb-4">
        <Brain className="h-6 w-6 text-emerald-400" />
        <h3 className="text-lg font-semibold text-white">{t('predictionTitle')}</h3>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-4">
          <p className="text-slate-400 text-sm mb-1">{t('predictedPrice')}</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(prediction.predicted_price, currency)}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4">
          <p className="text-slate-400 text-sm mb-1">{t('trendDirection')}</p>
          <div className={`flex items-center gap-2 ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
            {isUp ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
            <span className="text-xl font-bold capitalize">{t(prediction.trend)}</span>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-400">{t('modelConfidence')}</span>
          <span className="text-white font-medium">{confidencePercent}%</span>
        </div>
        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400 pt-4 border-t border-slate-700">
        <span>
          {t('modelLabel')}:{' '}
          <span className="text-slate-300">
            {prediction.model_used === 'rf' ? t('randomForest') : t('linear')}
          </span>
        </span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-slate-700/30 rounded">
          <p className="text-xs text-slate-400">RMSE</p>
          <p className="text-sm text-white font-mono">{metrics.rmse.toFixed(2)}</p>
        </div>
        <div className="text-center p-2 bg-slate-700/30 rounded">
          <p className="text-xs text-slate-400">MAE</p>
          <p className="text-sm text-white font-mono">{metrics.mae.toFixed(2)}</p>
        </div>
        <div className="text-center p-2 bg-slate-700/30 rounded">
          <p className="text-xs text-slate-400">R²</p>
          <p className="text-sm text-white font-mono">{metrics.r2.toFixed(3)}</p>
        </div>
      </div>
    </div>
  );
}
