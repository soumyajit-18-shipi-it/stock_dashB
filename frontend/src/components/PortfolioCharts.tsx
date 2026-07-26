import { Activity, Grid3X3, PieChart, Scale } from 'lucide-react';
import { useMemo, useState } from 'react';

import { LazyPlot } from './LazyPlot';

import type { PortfolioAnalysis } from '../types';
import type { Layout } from 'plotly.js-dist-min';

interface PortfolioChartsProps {
  analysis: PortfolioAnalysis;
}

const chartLayout: Partial<Layout> = {
  autosize: true,
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#cbd5e1', size: 11 },
  margin: { l: 50, r: 20, t: 30, b: 50 },
  xaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  yaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  showlegend: true,
  legend: { orientation: 'h', y: -0.2 },
};

const chartColors = ['#10b981', '#22d3ee', '#f59e0b', '#f43f5e', '#a78bfa', '#84cc16'];

export function PortfolioCharts({ analysis }: PortfolioChartsProps) {
  const [tab, setTab] = useState<'allocation' | 'risk' | 'optimization'>(
    'allocation'
  );
  const timelineData = useMemo(() => {
    const tickers = analysis.holdings.map((item) => item.ticker);
    return tickers.map((ticker, index) => ({
      type: 'scatter',
      mode: 'lines',
      stackgroup: 'one',
      groupnorm: 'percent',
      name: ticker,
      x: analysis.allocation_timeline.map((item) => item.date),
      y: analysis.allocation_timeline.map((item) => (item.weights[ticker] || 0) * 100),
      line: { color: chartColors[index % chartColors.length], width: 1 },
      hovertemplate: `${ticker}: %{y:.1f}%<extra></extra>`,
    }));
  }, [analysis]);

  return (
    <section className="border-t border-slate-700 pt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-white">Portfolio diagnostics</h2>
        <div className="inline-flex rounded-md border border-slate-700 bg-slate-900 p-1">
          <button
            type="button"
            onClick={() => setTab('allocation')}
            className={`flex items-center gap-2 rounded px-3 py-2 text-sm ${
              tab === 'allocation' ? 'bg-slate-700 text-cyan-300' : 'text-slate-400'
            }`}
          >
            <PieChart className="h-4 w-4" />
            Allocation
          </button>
          <button
            type="button"
            onClick={() => setTab('risk')}
            className={`flex items-center gap-2 rounded px-3 py-2 text-sm ${
              tab === 'risk' ? 'bg-slate-700 text-amber-300' : 'text-slate-400'
            }`}
          >
            <Grid3X3 className="h-4 w-4" />
            Risk
          </button>
          <button
            type="button"
            onClick={() => setTab('optimization')}
            className={`flex items-center gap-2 rounded px-3 py-2 text-sm ${
              tab === 'optimization' ? 'bg-slate-700 text-emerald-300' : 'text-slate-400'
            }`}
          >
            <Scale className="h-4 w-4" />
            Optimization
          </button>
        </div>
      </div>

      {tab === 'allocation' && (
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <ChartPanel title="Sector allocation">
            <LazyPlot
              data={[
                {
                  type: 'pie',
                  labels: Object.keys(analysis.sector_exposure),
                  values: Object.values(analysis.sector_exposure),
                  hole: 0.55,
                  marker: { colors: chartColors },
                  textinfo: 'label+percent',
                  hovertemplate: '%{label}: %{percent}<extra></extra>',
                },
              ] as never}
              layout={{ ...chartLayout, margin: { l: 15, r: 15, t: 20, b: 20 } }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <ChartPanel title="Holding treemap">
            <LazyPlot
              data={[
                {
                  type: 'treemap',
                  labels: analysis.holdings.map((item) => item.ticker),
                  parents: analysis.holdings.map(() => ''),
                  values: analysis.holdings.map((item) => item.weight),
                  textinfo: 'label+percent parent',
                  marker: { colors: chartColors },
                  hovertemplate: '%{label}: %{percentRoot:.1%}<extra></extra>',
                },
              ] as never}
              layout={{ ...chartLayout, margin: { l: 10, r: 10, t: 10, b: 10 } }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <div className="lg:col-span-2">
            <ChartPanel title="Allocation timeline">
              <LazyPlot
                data={timelineData as never}
                layout={{
                  ...chartLayout,
                  yaxis: {
                    gridcolor: '#334155',
                    title: { text: 'Weight %' },
                    range: [0, 100],
                  },
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
              />
            </ChartPanel>
          </div>
        </div>
      )}

      {tab === 'risk' && (
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <ChartPanel title="Correlation heatmap">
            <LazyPlot
              data={[
                {
                  type: 'heatmap',
                  x: analysis.correlation_matrix.tickers,
                  y: analysis.correlation_matrix.tickers,
                  z: analysis.correlation_matrix.values,
                  zmin: -1,
                  zmax: 1,
                  colorscale: [
                    [0, '#0891b2'],
                    [0.5, '#e2e8f0'],
                    [1, '#e11d48'],
                  ],
                  hovertemplate: '%{x} / %{y}: %{z:.2f}<extra></extra>',
                },
              ] as never}
              layout={{ ...chartLayout, yaxis: { autorange: 'reversed' } }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <ChartPanel title="Risk contribution">
            <LazyPlot
              data={[
                {
                  type: 'bar',
                  x: analysis.holdings.map((item) => item.ticker),
                  y: analysis.holdings.map((item) => item.risk_contribution * 100),
                  marker: {
                    color: analysis.holdings.map((item) =>
                      item.risk_contribution > item.weight ? '#f43f5e' : '#f59e0b'
                    ),
                  },
                  hovertemplate: '%{x}: %{y:.1f}%<extra></extra>',
                },
              ] as never}
              layout={{
                ...chartLayout,
                yaxis: {
                  gridcolor: '#334155',
                  title: { text: 'Variance contribution %' },
                },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <div className="lg:col-span-2 grid gap-5 md:grid-cols-3">
            <ExposureList title="Country" values={analysis.country_exposure} />
            <ExposureList title="Market cap" values={analysis.market_cap_exposure} />
            <ExposureList title="Factors" values={analysis.factor_exposure} factor />
          </div>
        </div>
      )}

      {tab === 'optimization' && (
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <ChartPanel title="Efficient frontier">
            <LazyPlot
              data={[
                {
                  type: 'scatter',
                  mode: 'markers+lines',
                  x: analysis.efficient_frontier.map((point) => point.volatility * 100),
                  y: analysis.efficient_frontier.map((point) => point.expected_return * 100),
                  marker: {
                    color: analysis.efficient_frontier.map((point) => point.sharpe_ratio),
                    colorscale: 'Viridis',
                    size: 8,
                    colorbar: { title: 'Sharpe' },
                  },
                  hovertemplate: 'Vol %{x:.1f}%<br>Return %{y:.1f}%<extra></extra>',
                },
                {
                  type: 'scatter',
                  mode: 'markers',
                  name: 'Current',
                  x: [analysis.metrics.expected_volatility * 100],
                  y: [analysis.metrics.expected_return * 100],
                  marker: { color: '#f43f5e', size: 13, symbol: 'diamond' },
                },
              ] as never}
              layout={{
                ...chartLayout,
                xaxis: {
                  gridcolor: '#334155',
                  title: { text: 'Volatility %' },
                },
                yaxis: {
                  gridcolor: '#334155',
                  title: { text: 'Expected return %' },
                },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <ChartPanel title="Suggested allocation">
            <LazyPlot
              data={[
                {
                  type: 'bar',
                  name: 'Current',
                  x: analysis.rebalancing.map((item) => item.ticker),
                  y: analysis.rebalancing.map((item) => item.current_weight * 100),
                  marker: { color: '#64748b' },
                },
                {
                  type: 'bar',
                  name: 'Target',
                  x: analysis.rebalancing.map((item) => item.ticker),
                  y: analysis.rebalancing.map((item) => item.target_weight * 100),
                  marker: { color: '#10b981' },
                },
              ] as never}
              layout={{
                ...chartLayout,
                barmode: 'group',
                yaxis: {
                  gridcolor: '#334155',
                  title: { text: 'Weight %' },
                },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </ChartPanel>
          <div className="lg:col-span-2 grid gap-px overflow-hidden rounded-md border border-slate-700 bg-slate-700 sm:grid-cols-4">
            <SimulationMetric
              label="5th percentile"
              value={`${((analysis.monte_carlo.percentile_5 - 1) * 100).toFixed(1)}%`}
              tone="text-rose-300"
            />
            <SimulationMetric
              label="Median"
              value={`${((analysis.monte_carlo.percentile_50 - 1) * 100).toFixed(1)}%`}
              tone="text-cyan-300"
            />
            <SimulationMetric
              label="95th percentile"
              value={`${((analysis.monte_carlo.percentile_95 - 1) * 100).toFixed(1)}%`}
              tone="text-emerald-300"
            />
            <SimulationMetric
              label="Loss probability"
              value={`${(analysis.monte_carlo.loss_probability * 100).toFixed(1)}%`}
              tone="text-amber-300"
            />
          </div>
        </div>
      )}
    </section>
  );
}

function ChartPanel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <Activity className="h-4 w-4 text-cyan-400" />
        {title}
      </h3>
      <div className="mt-2 h-80">{children}</div>
    </div>
  );
}

function ExposureList({
  title,
  values,
  factor = false,
}: {
  title: string;
  values: Record<string, number>;
  factor?: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
      <h3 className="text-sm font-semibold text-slate-200">{title} exposure</h3>
      <div className="mt-3 space-y-3">
        {Object.entries(values).map(([name, value]) => (
          <div key={name}>
            <div className="flex justify-between text-xs text-slate-400">
              <span className="capitalize">{name.replace(/_/g, ' ')}</span>
              <span>{factor ? value.toFixed(2) : `${(value * 100).toFixed(1)}%`}</span>
            </div>
            {!factor && (
              <div className="mt-1 h-1.5 rounded-full bg-slate-700">
                <div
                  className="h-full rounded-full bg-cyan-500"
                  style={{ width: `${Math.min(100, value * 100)}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SimulationMetric({
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
      <p className={`mt-1 text-lg font-semibold ${tone}`}>{value}</p>
    </div>
  );
}
