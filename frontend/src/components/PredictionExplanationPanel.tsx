import { BarChart3, GitBranch, Info } from 'lucide-react';
import { useState } from 'react';

import { LazyPlot } from './LazyPlot';

import type { PredictionExplanation } from '../types';

interface PredictionExplanationPanelProps {
  explanation: PredictionExplanation | null | undefined;
}

export function PredictionExplanationPanel({
  explanation,
}: PredictionExplanationPanelProps) {
  const [view, setView] = useState<'ranking' | 'waterfall'>('ranking');

  if (!explanation) {
    return (
      <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-5">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Info className="h-4 w-4" />
          Prediction explanation is unavailable for this run.
        </div>
      </section>
    );
  }

  const topFeatures = explanation.features.slice(0, 8);
  const chartData =
    view === 'ranking'
      ? [
          {
            type: 'bar',
            orientation: 'h',
            x: [...topFeatures].reverse().map((item) => item.contribution),
            y: [...topFeatures].reverse().map((item) => item.display_name),
            marker: {
              color: [...topFeatures]
                .reverse()
                .map((item) => (item.contribution >= 0 ? '#10b981' : '#f43f5e')),
            },
            hovertemplate: '%{y}<br>Contribution: %{x:.3f}<extra></extra>',
          },
        ]
      : [
          {
            type: 'waterfall',
            x: ['Base', ...topFeatures.map((item) => item.display_name), 'Prediction'],
            y: [
              explanation.base_value,
              ...topFeatures.map((item) => item.contribution),
              explanation.predicted_price,
            ],
            measure: [
              'absolute',
              ...topFeatures.map(() => 'relative'),
              'total',
            ],
            connector: { line: { color: '#64748b' } },
            increasing: { marker: { color: '#10b981' } },
            decreasing: { marker: { color: '#f43f5e' } },
            totals: { marker: { color: '#22d3ee' } },
            hovertemplate: '%{x}<br>%{y:.3f}<extra></extra>',
          },
        ];

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Prediction explanation
          </p>
          <h3 className="mt-1 text-lg font-semibold text-white">
            {explanation.method}
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            {explanation.provider_status === 'available'
              ? 'Exact additive explanation'
              : 'Degraded local explanation'}
          </p>
        </div>
        <div className="inline-flex rounded-md border border-slate-700 bg-slate-950 p-1">
          <button
            type="button"
            title="Feature ranking"
            onClick={() => setView('ranking')}
            className={`rounded p-2 ${
              view === 'ranking' ? 'bg-slate-700 text-cyan-300' : 'text-slate-400'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
          </button>
          <button
            type="button"
            title="Waterfall"
            onClick={() => setView('waterfall')}
            className={`rounded p-2 ${
              view === 'waterfall' ? 'bg-slate-700 text-cyan-300' : 'text-slate-400'
            }`}
          >
            <GitBranch className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-px overflow-hidden rounded-md border border-slate-700 bg-slate-700">
        <div className="bg-slate-900 p-3">
          <p className="text-xs text-slate-400">Prediction</p>
          <p className="mt-1 text-base font-semibold text-white">
            {explanation.predicted_price.toFixed(2)}
          </p>
        </div>
        <div className="bg-slate-900 p-3">
          <p className="text-xs text-slate-400">Expected return</p>
          <p
            className={`mt-1 text-base font-semibold ${
              explanation.expected_return >= 0 ? 'text-emerald-300' : 'text-rose-300'
            }`}
          >
            {(explanation.expected_return * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-slate-900 p-3">
          <p className="text-xs text-slate-400">80% interval</p>
          <p className="mt-1 text-sm font-semibold text-cyan-300">
            {explanation.uncertainty_lower.toFixed(2)}-
            {explanation.uncertainty_upper.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="mt-4 h-80 w-full">
        <LazyPlot
          data={chartData as never}
          layout={{
            autosize: true,
            margin: { l: view === 'ranking' ? 145 : 45, r: 15, t: 15, b: 80 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { color: '#cbd5e1', size: 11 },
            xaxis: { gridcolor: '#334155', zerolinecolor: '#64748b' },
            yaxis: { gridcolor: '#334155', automargin: true },
            showlegend: false,
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
        />
      </div>
    </section>
  );
}
