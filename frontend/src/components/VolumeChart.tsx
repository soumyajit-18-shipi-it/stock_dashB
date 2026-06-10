import Plot from 'react-plotly.js';
import type { StockPricePoint } from '../types';

interface VolumeChartProps {
  data: StockPricePoint[];
}

export function VolumeChart({ data }: VolumeChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700">
        <p className="text-slate-400">No volume data available</p>
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const volumes = data.map((d) => d.volume);
  const colors = volumes.map((_, i) => {
    if (i === 0) return '#3b82f6';
    return volumes[i] >= volumes[i - 1] ? '#10b981' : '#ef4444';
  });

  const trace: Plotly.Data = {
    x: dates,
    y: volumes,
    type: 'bar',
    marker: { color: colors },
    hovertemplate: '<b>Date:</b> %{x}<br><b>Volume:</b> %{y:,.0f}<extra></extra>',
  };

  const layout: Partial<Plotly.Layout> = {
    title: {
      text: 'Volume',
      font: { color: '#f1f5f9', size: 14 },
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8' },
    xaxis: {
      gridcolor: '#334155',
      linecolor: '#475569',
      tickfont: { color: '#94a3b8' },
    },
    yaxis: {
      gridcolor: '#334155',
      linecolor: '#475569',
      tickfont: { color: '#94a3b8' },
      tickformat: '.2s',
    },
    margin: { l: 40, r: 20, t: 30, b: 40 },
    bargap: 0.1,
  };

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: false,
    displaylogo: false,
  };

  return (
    <div className="w-full h-48 bg-slate-800/30 rounded-xl border border-slate-700 p-4">
      <Plot data={[trace]} layout={layout} config={config} className="w-full h-full" />
    </div>
  );
}
