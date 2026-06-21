import { Plus, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import {
  SearchBar,
  StockChart,
  VolumeChart,
  PredictionCard,
  CompanyProfileCard,
  DateRangeSelector,
  ModelToggle,
  LoadingSkeleton,
  ErrorMessage,
  EmptyState,
  AskAIDrawer,
  AIReportButton,
} from '../components';
import { useStock, useWatchlist } from '../hooks/useStock';
import { useStore } from '../store/stock_store';

export function Dashboard() {
  const { ticker, model } = useStore();
  const { t } = useTranslation();
  const { watchlist, add } = useWatchlist();
  const { data: stockData, isLoading, error } = useStock();

  const isInWatchlist = watchlist.some((item) => item.ticker === ticker);

  const handleAddToWatchlist = async () => {
    if (ticker && !isInWatchlist && stockData) {
      await add(ticker, stockData.profile.name);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <SearchBar />
        </div>

        {!ticker ? (
          <EmptyState />
        ) : isLoading ? (
          <LoadingSkeleton />
        ) : error ? (
          <ErrorMessage message={t('fetchStockError')} />
        ) : stockData ? (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4">
                <DateRangeSelector />
                <ModelToggle />
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-400">
                  {t('modelLabel')}:{' '}
                  <span className="text-emerald-400">
                    {model === 'rf' ? t('randomForest') : t('linear')}
                  </span>
                </span>
                {isInWatchlist ? (
                  <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/20 px-4 py-2 rounded-lg">
                    <Check className="h-4 w-4" />
                    <span className="text-sm font-medium">{t('inWatchlist')}</span>
                  </div>
                ) : (
                  <button
                    onClick={handleAddToWatchlist}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  >
                    <Plus className="h-4 w-4" />
                    {t('addToWatchlist')}
                  </button>
                )}
                <AIReportButton stockData={stockData} />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <StockChart
                  data={stockData.history}
                  stockData={stockData}
                  title={t('priceHistory', { ticker: stockData.profile.ticker })}
                />
                <VolumeChart data={stockData.history} />
              </div>

              <div className="space-y-6">
                <CompanyProfileCard profile={stockData.profile} />
                <PredictionCard
                  prediction={stockData.prediction}
                  metrics={stockData.metrics}
                  stockData={stockData}
                />
              </div>
            </div>
            <AskAIDrawer stockData={stockData} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
