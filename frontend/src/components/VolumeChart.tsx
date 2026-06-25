import { useTranslation } from 'react-i18next';

import { LazyPlot } from './LazyPlot';
import { useUIStore } from '../store/ui_store';

import type { StockPricePoint } from '../types';

interface VolumeChartProps {
  data: StockPricePoint[];
}

export function VolumeChart({ data }: VolumeChartProps) {
  const { t } = useTranslation();
  const { darkMode } = useUIStore();
  const chartTheme = darkMode
    ? {
        paper: 'transparent',
        plot: 'transparent',
        font: '#94a3b8',
        title: '#f1f5f9',
        grid: '#334155',
        line: '#475569',
      }
    : {
        paper: '#ffffff',
        plot: '#ffffff',
        font: '#475569',
        title: '#0f172a',
        grid: '#e2e8f0',
        line: '#cbd5e1',
      };

  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700">
        <p className="text-slate-400">{t('noVolumeData')}</p>
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const volumes = data.map((d) => d.volume);
  const colors = volumes.map((_, i) => {
    if (i === 0) return '#3b82f6';
    const current = volumes[i];
    const prev = volumes[i - 1];
    if (current === undefined || prev === undefined) return '#3b82f6';
    return current >= prev ? '#10b981' : '#ef4444';
  });

  const trace: Plotly.Data = {
    x: dates,
    y: volumes,
    type: 'bar',
    marker: { color: colors },
    hovertemplate: `<b>${t('date')}:</b> %{x}<br><b>${t('volume')}:</b> %{y:,.0f}<extra></extra>`,
  };

  const layout: Partial<Plotly.Layout> = {
    title: {
      text: t('volume'),
      font: { color: chartTheme.title, size: 14 },
    },
    paper_bgcolor: chartTheme.paper,
    plot_bgcolor: chartTheme.plot,
    font: { color: chartTheme.font },
    xaxis: {
      gridcolor: chartTheme.grid,
      linecolor: chartTheme.line,
      tickfont: { color: chartTheme.font },
      automargin: true,
    },
    yaxis: {
      gridcolor: chartTheme.grid,
      linecolor: chartTheme.line,
      tickfont: { color: chartTheme.font, size: 10 },
      tickformat: '.2s',
      automargin: true,
    },
    margin: { l: 80, r: 20, t: 30, b: 40 },
    bargap: 0.1,
  };

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displayModeBar: false,
    displaylogo: false,
  };

  return (
    <div className="w-full h-48 bg-slate-800/30 rounded-xl border border-slate-700 p-4">
      <LazyPlot data={[trace]} layout={layout} config={config} className="w-full h-full" />
    </div>
  );
}
