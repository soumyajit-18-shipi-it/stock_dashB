import { useTranslation } from 'react-i18next';

import { LazyPlot } from './LazyPlot';
import { useUIStore } from '../store/ui_store';
import { currencyForStock } from '../utils/format';

import type { StockPricePoint, StockResponse } from '../types';

interface StockChartProps {
  data: StockPricePoint[];
  title?: string;
  stockData?: StockResponse;
}

export function StockChart({ data, title, stockData }: StockChartProps) {
  const { t } = useTranslation();
  const { darkMode } = useUIStore();
  const currency = currencyForStock(stockData);
  const symbol = currency === 'INR' ? 'INR ' : '$';
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
      <div className="h-96 flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700">
        <p className="text-slate-400">{t('noChartData')}</p>
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
      name: t('close'),
      line: { color: '#10b981', width: 2 },
      hovertemplate: `<b>${t('date')}:</b> %{x}<br><b>${t('close')}:</b> ${symbol}%{y:.2f}<extra></extra>`,
    },
    {
      x: dates,
      y: ma7,
      type: 'scatter',
      mode: 'lines',
      name: 'MA7',
      line: { color: '#f59e0b', width: 1.5, dash: 'dot' },
      hovertemplate: `<b>${t('date')}:</b> %{x}<br><b>MA7:</b> ${symbol}%{y:.2f}<extra></extra>`,
    },
    {
      x: dates,
      y: ma21,
      type: 'scatter',
      mode: 'lines',
      name: 'MA21',
      line: { color: '#8b5cf6', width: 1.5, dash: 'dash' },
      hovertemplate: `<b>${t('date')}:</b> %{x}<br><b>MA21:</b> ${symbol}%{y:.2f}<extra></extra>`,
    },
  ];

  const layout: Partial<Plotly.Layout> = {
    title: {
      text: title || t('price'),
      font: { color: chartTheme.title, size: 16 },
    },
    paper_bgcolor: chartTheme.paper,
    plot_bgcolor: chartTheme.plot,
    font: { color: chartTheme.font },
    xaxis: {
      title: { text: t('date') },
      gridcolor: chartTheme.grid,
      linecolor: chartTheme.line,
      tickfont: { color: chartTheme.font },
      automargin: true,
    },
    yaxis: {
      title: { text: `${t('price')} (${currency})`, standoff: 25 },
      gridcolor: chartTheme.grid,
      linecolor: chartTheme.line,
      tickfont: { color: chartTheme.font, size: 10 },
      tickprefix: symbol,
      automargin: true,
    },
    legend: {
      orientation: 'h',
      y: -0.2,
      font: { color: chartTheme.font, size: 10 },
    },
    margin: { l: 100, r: 40, t: 40, b: 80 },
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
      <LazyPlot data={traces} layout={layout} config={config} className="w-full h-full" />
    </div>
  );
}
