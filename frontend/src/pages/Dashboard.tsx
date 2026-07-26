import { Plus, Check } from 'lucide-react';
import { useState } from 'react';
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
  RecommendationCard,
  PredictionExplanationPanel,
} from '../components';
import { useRecommendation } from '../hooks/useRecommendation';
import { useStock, useWatchlist } from '../hooks/useStock';
import { api } from '../services/api_client';
import { useStore } from '../store/stock_store';

import type { InvestmentHorizon, RiskTolerance } from '../types';

export function Dashboard() {
  const { ticker, model, dateRange } = useStore();
  const { t } = useTranslation();
  const { watchlist, add } = useWatchlist();
  const { data: stockData, isLoading, error, refetch } = useStock();
  const [watchlistError, setWatchlistError] = useState('');
  const [riskTolerance, setRiskTolerance] =
    useState<RiskTolerance>('balanced');
  const [horizon, setHorizon] = useState<InvestmentHorizon>('medium');
  const [llmExplanation, setLlmExplanation] = useState('');
  const [isExplaining, setIsExplaining] = useState(false);
  const {
    data: recommendation,
    isLoading: recommendationLoading,
    error: recommendationError,
  } = useRecommendation(
    ticker,
    dateRange,
    model,
    riskTolerance,
    horizon
  );

  const explainRecommendation = async () => {
    if (!recommendation) return;
    setIsExplaining(true);
    setLlmExplanation('');
    try {
      setLlmExplanation(await api.explainRecommendation(recommendation));
    } catch (caught) {
      setLlmExplanation(
        caught instanceof Error ? caught.message : 'AI explanation failed'
      );
    } finally {
      setIsExplaining(false);
    }
  };

  const isInWatchlist = watchlist.some((item) => item.ticker === ticker);

  const handleAddToWatchlist = async () => {
    if (ticker && !isInWatchlist && stockData) {
      setWatchlistError('');
      try {
        await add(ticker, stockData.profile.name);
      } catch (err) {
        setWatchlistError(
          err instanceof Error ? err.message : 'Failed to save watchlist item.'
        );
      }
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
          <ErrorMessage message={error instanceof Error ? error.message : t('fetchStockError')} onRetry={() => refetch()} />
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
            {watchlistError && (
              <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                {watchlistError}
              </p>
            )}

            <RecommendationCard
              recommendation={recommendation}
              isLoading={recommendationLoading}
              error={
                recommendationError instanceof Error
                  ? recommendationError
                  : null
              }
              riskTolerance={riskTolerance}
              horizon={horizon}
              onRiskToleranceChange={(value) => {
                setRiskTolerance(value);
                setLlmExplanation('');
              }}
              onHorizonChange={(value) => {
                setHorizon(value);
                setLlmExplanation('');
              }}
              onExplain={() => void explainRecommendation()}
              isExplaining={isExplaining}
              llmExplanation={llmExplanation}
            />

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
            <PredictionExplanationPanel
              explanation={recommendation?.prediction_explanation}
            />
          </div>
        ) : null}
      </div>
      <AskAIDrawer stockData={stockData || null} />
    </div>
  );
}
