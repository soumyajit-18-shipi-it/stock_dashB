import {
  AlertTriangle,
  Bot,
  Briefcase,
  FileUp,
  Loader2,
  Plus,
  Save,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { useRef, useState } from 'react';

import { PortfolioCharts } from '../components';
import { api } from '../services/api_client';

import type {
  PortfolioAnalysis,
  PortfolioHoldingInput,
} from '../types';

interface EditableHolding extends PortfolioHoldingInput {
  id: string;
}

const initialHoldings: EditableHolding[] = [
  { id: 'holding-1', ticker: 'AAPL', quantity: 10 },
  { id: 'holding-2', ticker: 'MSFT', quantity: 8 },
];

export function PortfolioDashboard() {
  const [holdings, setHoldings] = useState<EditableHolding[]>(initialHoldings);
  const [allocationMode, setAllocationMode] = useState<'quantity' | 'weight'>(
    'quantity'
  );
  const [range, setRange] = useState<'1y' | '5y'>('5y');
  const [analysis, setAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [portfolioName, setPortfolioName] = useState('Core portfolio');
  const [saveStatus, setSaveStatus] = useState('');
  const [aiExplanation, setAiExplanation] = useState('');
  const [isExplaining, setIsExplaining] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const addHolding = () => {
    setHoldings((current) => [
      ...current,
      {
        id: `holding-${Date.now()}`,
        ticker: '',
        ...(allocationMode === 'quantity' ? { quantity: 1 } : { weight: 0.1 }),
      },
    ]);
  };

  const updateHolding = (
    id: string,
    field: 'ticker' | 'quantity' | 'weight' | 'average_cost',
    value: string
  ) => {
    setHoldings((current) =>
      current.map((item) => {
        if (item.id !== id) return item;
        if (field === 'ticker') return { ...item, ticker: value.toUpperCase() };
        const number = value === '' ? undefined : Number(value);
        if (field === 'weight') {
          return { ...item, weight: number === undefined ? undefined : number / 100 };
        }
        return { ...item, [field]: number };
      })
    );
  };

  const switchMode = (mode: 'quantity' | 'weight') => {
    setAllocationMode(mode);
    setHoldings((current) =>
      current.map((item) => ({
        id: item.id,
        ticker: item.ticker,
        average_cost: item.average_cost,
        ...(mode === 'quantity' ? { quantity: item.quantity || 1 } : { weight: item.weight || 1 / current.length }),
      }))
    );
  };

  const normalizedHoldings = (): PortfolioHoldingInput[] =>
    holdings
      .filter((item) => item.ticker.trim())
      .map(({ ticker, quantity, weight, average_cost }) => ({
        ticker: ticker.trim().toUpperCase(),
        ...(allocationMode === 'quantity' ? { quantity } : { weight }),
        ...(average_cost !== undefined ? { average_cost } : {}),
      }));

  const analyze = async () => {
    setError('');
    setSaveStatus('');
    setAiExplanation('');
    setIsAnalyzing(true);
    try {
      const result = await api.analyzePortfolio(normalizedHoldings(), range);
      setAnalysis(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Portfolio analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analyzeWatchlist = async () => {
    setError('');
    setSaveStatus('');
    setAiExplanation('');
    setIsAnalyzing(true);
    try {
      const result = await api.analyzeWatchlist(range);
      setAnalysis(result);
      setHoldings(
        result.holdings.map((item, index) => ({
          id: `watchlist-${index}`,
          ticker: item.ticker,
          weight: item.weight,
        }))
      );
      setAllocationMode('weight');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Watchlist analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const uploadCsv = async (file?: File) => {
    if (!file) return;
    setError('');
    try {
      const parsed = await api.parsePortfolioCsv(await file.text());
      setHoldings(
        parsed.map((item, index) => ({
          ...item,
          id: `csv-${index}-${item.ticker}`,
        }))
      );
      setAllocationMode(parsed.every((item) => item.weight !== undefined) ? 'weight' : 'quantity');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'CSV import failed');
    } finally {
      if (fileInput.current) fileInput.current.value = '';
    }
  };

  const savePortfolio = async () => {
    if (!analysis) return;
    setSaveStatus('');
    try {
      await api.savePortfolio(portfolioName, normalizedHoldings(), analysis);
      setSaveStatus('Saved');
    } catch (caught) {
      setSaveStatus(caught instanceof Error ? caught.message : 'Save failed');
    }
  };

  const explain = async () => {
    if (!analysis) return;
    setIsExplaining(true);
    setAiExplanation('');
    try {
      setAiExplanation(await api.explainPortfolio(analysis));
    } catch (caught) {
      setAiExplanation(
        caught instanceof Error ? caught.message : 'AI explanation failed'
      );
    } finally {
      setIsExplaining(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2 text-cyan-300">
              <Briefcase className="h-5 w-5" />
              <span className="text-xs font-medium uppercase tracking-wide">
                Portfolio intelligence
              </span>
            </div>
            <h1 className="mt-2 text-2xl font-bold text-white">Portfolio Analyzer</h1>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">
              History
              <select
                value={range}
                onChange={(event) => setRange(event.target.value as '1y' | '5y')}
                className="ml-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"
              >
                <option value="1y">1 year</option>
                <option value="5y">5 years</option>
              </select>
            </label>
          </div>
        </header>

        <section className="py-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex rounded-md border border-slate-700 bg-slate-900 p-1">
              <button
                type="button"
                onClick={() => switchMode('quantity')}
                className={`rounded px-3 py-2 text-sm ${
                  allocationMode === 'quantity'
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400'
                }`}
              >
                Shares
              </button>
              <button
                type="button"
                onClick={() => switchMode('weight')}
                className={`rounded px-3 py-2 text-sm ${
                  allocationMode === 'weight'
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400'
                }`}
              >
                Weights
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                ref={fileInput}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(event) => void uploadCsv(event.target.files?.[0])}
              />
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
              >
                <FileUp className="h-4 w-4" />
                CSV
              </button>
              <button
                type="button"
                onClick={() => void analyzeWatchlist()}
                className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
              >
                <Sparkles className="h-4 w-4 text-amber-300" />
                Watchlist
              </button>
              <button
                type="button"
                onClick={addHolding}
                className="flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
              >
                <Plus className="h-4 w-4" />
                Holding
              </button>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto rounded-lg border border-slate-700">
            <table className="min-w-full divide-y divide-slate-700 text-sm">
              <thead className="bg-slate-900 text-left text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">
                    {allocationMode === 'quantity' ? 'Shares' : 'Weight %'}
                  </th>
                  <th className="px-4 py-3">Average cost</th>
                  <th className="w-14 px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950">
                {holdings.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3">
                      <input
                        value={item.ticker}
                        onChange={(event) =>
                          updateHolding(item.id, 'ticker', event.target.value)
                        }
                        className="w-32 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-medium text-white"
                        maxLength={20}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <input
                        type="number"
                        min="0.0001"
                        step="any"
                        value={
                          allocationMode === 'quantity'
                            ? item.quantity ?? ''
                            : item.weight !== undefined
                              ? item.weight * 100
                              : ''
                        }
                        onChange={(event) =>
                          updateHolding(
                            item.id,
                            allocationMode,
                            event.target.value
                          )
                        }
                        className="w-32 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={item.average_cost ?? ''}
                        onChange={(event) =>
                          updateHolding(item.id, 'average_cost', event.target.value)
                        }
                        className="w-32 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        title="Remove holding"
                        onClick={() =>
                          setHoldings((current) =>
                            current.filter((holding) => holding.id !== item.id)
                          )
                        }
                        className="rounded p-2 text-slate-400 hover:bg-rose-500/10 hover:text-rose-300"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            {error ? (
              <div className="flex items-center gap-2 text-sm text-rose-300">
                <AlertTriangle className="h-4 w-4" />
                {error}
              </div>
            ) : (
              <span className="text-xs text-slate-500">
                {holdings.length} holdings
              </span>
            )}
            <button
              type="button"
              disabled={isAnalyzing || holdings.length === 0}
              onClick={() => void analyze()}
              className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isAnalyzing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Briefcase className="h-4 w-4" />
              )}
              Analyze portfolio
            </button>
          </div>
        </section>

        {analysis && (
          <section className="space-y-6 border-t border-slate-800 py-6">
            <div className="grid gap-px overflow-hidden rounded-md border border-slate-700 bg-slate-700 sm:grid-cols-3 lg:grid-cols-6">
              <Metric label="Portfolio" value={analysis.metrics.portfolio_score.toFixed(0)} tone="text-cyan-300" />
              <Metric label="Diversification" value={analysis.metrics.diversification_score.toFixed(0)} tone="text-emerald-300" />
              <Metric label="Risk" value={analysis.metrics.risk_score.toFixed(0)} tone="text-amber-300" />
              <Metric label="Expected return" value={`${(analysis.metrics.expected_return * 100).toFixed(1)}%`} tone={analysis.metrics.expected_return >= 0 ? 'text-emerald-300' : 'text-rose-300'} />
              <Metric label="Volatility" value={`${(analysis.metrics.expected_volatility * 100).toFixed(1)}%`} tone="text-amber-300" />
              <Metric label="Sharpe" value={analysis.metrics.sharpe_ratio.toFixed(2)} tone="text-violet-300" />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="min-w-full divide-y divide-slate-700 text-sm">
                  <thead className="bg-slate-900 text-left text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Holding</th>
                      <th className="px-4 py-3">Weight</th>
                      <th className="px-4 py-3">Return</th>
                      <th className="px-4 py-3">Volatility</th>
                      <th className="px-4 py-3">Risk contribution</th>
                      <th className="px-4 py-3">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {analysis.holdings.map((item) => (
                      <tr key={item.ticker} className="text-slate-300">
                        <td className="px-4 py-3 font-semibold text-white">
                          {item.ticker}
                          <span className="ml-2 text-xs font-normal text-slate-500">
                            {item.sector}
                          </span>
                        </td>
                        <td className="px-4 py-3">{(item.weight * 100).toFixed(1)}%</td>
                        <td className={`px-4 py-3 ${item.annual_return >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                          {(item.annual_return * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3">{(item.annual_volatility * 100).toFixed(1)}%</td>
                        <td className="px-4 py-3">{(item.risk_contribution * 100).toFixed(1)}%</td>
                        <td className="px-4 py-3">{item.holding_score.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-5">
                <h2 className="text-sm font-semibold text-white">Largest risks</h2>
                <ul className="mt-3 space-y-2">
                  {analysis.largest_risks.map((risk) => (
                    <li key={risk} className="flex gap-2 text-sm text-slate-300">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                      {risk}
                    </li>
                  ))}
                </ul>
                <div className="mt-5 grid grid-cols-2 gap-4 border-t border-slate-700 pt-4 text-sm">
                  <div>
                    <p className="text-xs text-slate-500">Best holdings</p>
                    <p className="mt-1 text-emerald-300">{analysis.best_holdings.join(', ')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Weakest holdings</p>
                    <p className="mt-1 text-rose-300">{analysis.weakest_holdings.join(', ')}</p>
                  </div>
                </div>
              </div>
            </div>

            <PortfolioCharts analysis={analysis} />

            <div className="grid gap-4 border-t border-slate-700 pt-6 lg:grid-cols-[1fr_auto]">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <Bot className="h-4 w-4 text-violet-300" />
                  AI explanation
                </h2>
                {aiExplanation ? (
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                    {aiExplanation}
                  </p>
                ) : (
                  <div className="mt-3 space-y-1 text-sm text-slate-400">
                    {analysis.explanation.map((item) => (
                      <p key={item}>{item}</p>
                    ))}
                  </div>
                )}
              </div>
              <button
                type="button"
                disabled={isExplaining}
                onClick={() => void explain()}
                className="flex h-fit items-center gap-2 rounded-md border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-sm text-violet-200 hover:bg-violet-500/20 disabled:opacity-50"
              >
                {isExplaining ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
                Explain
              </button>
            </div>

            <div className="flex flex-wrap items-end justify-between gap-3 border-t border-slate-700 pt-5">
              <label className="text-xs text-slate-400">
                Portfolio name
                <input
                  value={portfolioName}
                  onChange={(event) => setPortfolioName(event.target.value)}
                  className="mt-1 block w-64 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"
                  maxLength={120}
                />
              </label>
              <div className="flex items-center gap-3">
                {saveStatus && <span className="text-sm text-slate-300">{saveStatus}</span>}
                <button
                  type="button"
                  onClick={() => void savePortfolio()}
                  className="flex items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
                >
                  <Save className="h-4 w-4" />
                  Save portfolio
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div className="bg-slate-900 p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${tone}`}>{value}</p>
    </div>
  );
}
