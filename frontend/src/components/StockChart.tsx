import Plot from 'react-plotly.js';
import type { StockPricePoint } from '../types';

interface StockChartProps {
  data: StockPricePoint[];
  title?: string;
}

export function StockChart({ data, title = 'Stock Price' }: StockChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700">
        <p className="text-slate-400">No chart data available</p>
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const close = data.map((d) => d.close);
  const ma7 = data.map((d) => d.ma7 ?? null);
  const ma21 = data.map((d) => d.ma21 ?? null);

  const traces: Plotly.Data[] = [
    {
      x: dates,
      y: close,
      type: 'scatter',
      mode: 'lines',
      name: 'Close',
      line: { color: '#10b981', width: 2 },
      hovertemplate: '<b>Date:</b> %{x}<br><b>Close:</b> $%{y:.2f}<extra></extra>',
    },
    {
      x: dates,
      y: ma7,
      type: 'scatter',
      mode: 'lines',
      name: 'MA7',
      line: { color: '#f59e0b', width: 1.5, dash: 'dot' },
      hovertemplate: '<b>Date:</b> %{x}<br><b>MA7:</b> $%{y:.2f}<extra></extra>',
    },
    {
      x: dates,
      y: ma21,
      type: 'scatter',
      mode: 'lines',
      name: 'MA21',
      line: { color: '#8b5cf6', width: 1.5, dash: 'dash' },
      hovertemplate: '<b>Date:</b> %{x}<br><b>MA21:</b> $%{y:.2f}<extra></extra>',
    },
  ];

  const layout: Partial<Plotly.Layout> = {
    title: {
      text: title,
      font: { color: '#f1f5f9', size: 16 },
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8' },
    xaxis: {
      title: { text: 'Date' },
      gridcolor: '#334155',
      linecolor: '#475569',
      tickfont: { color: '#94a3b8' },
    },
    yaxis: {
      title: { text: 'Price ($)' },
      gridcolor: '#334155',
      linecolor: '#475569',
      tickfont: { color: '#94a3b8' },
      tickprefix: '$',
    },
    legend: {
      orientation: 'h',
      y: -0.2,
      font: { color: '#94a3b8' },
    },
    margin: { l: 60, r: 40, t: 40, b: 80 },
    hovermode: 'x unified',
  };

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div className="w-full h-96 bg-slate-800/30 rounded-xl border border-slate-700 p-4">
      <Plot data={traces} layout={layout} config={config} className="w-full h-full" />
    </div>
  );
}
