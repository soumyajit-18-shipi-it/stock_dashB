import React from 'react';
import Plot from 'react-plotly.js';
import { useStock } from '../store/stock_store';

const StockChart: React.FC = () => {
  const { stockData } = useStock();

  if (!stockData) return null;

  const dates = stockData.history.map((h) => h.date);
  const closes = stockData.history.map((h) => h.close);
  const volumes = stockData.history.map((h) => h.volume);
  const ma7 = stockData.history.map((h) => h.ma7);
  const ma21 = stockData.history.map((h) => h.ma21);

  return (
    <div className="w-full bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div className="mb-4">
        <Plot
          data={[
            {
              x: dates,
              y: closes,
              type: 'scatter',
              mode: 'lines',
              name: 'Close Price',
              line: { color: '#2563eb', width: 2 },
            },
            {
              x: dates,
              y: ma7,
              type: 'scatter',
              mode: 'lines',
              name: '7-day MA',
              line: { color: '#f59e0b', width: 1.5, dash: 'dot' },
            },
            {
              x: dates,
              y: ma21,
              type: 'scatter',
              mode: 'lines',
              name: '21-day MA',
              line: { color: '#10b981', width: 1.5, dash: 'dot' },
            },
          ]}
          layout={{
            title: `${stockData.ticker} Price History`,
            autosize: true,
            height: 400,
            margin: { t: 40, r: 20, l: 40, b: 40 },
            xaxis: { title: 'Date', gridcolor: '#f3f4f6' },
            yaxis: { title: 'Price', gridcolor: '#f3f4f6' },
            legend: { orientation: 'h', y: -0.2 },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
          }}
          useResizeHandler={true}
          className="w-full"
        />
      </div>
      <div>
        <Plot
          data={[
            {
              x: dates,
              y: volumes,
              type: 'bar',
              name: 'Volume',
              marker: { color: '#94a3b8' },
            },
          ]}
          layout={{
            title: `${stockData.ticker} Trading Volume`,
            autosize: true,
            height: 200,
            margin: { t: 30, r: 20, l: 40, b: 40 },
            xaxis: { gridcolor: '#f3f4f6' },
            yaxis: { title: 'Volume', gridcolor: '#f3f4f6' },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
          }}
          useResizeHandler={true}
          className="w-full"
        />
      </div>
    </div>
  );
};

export default StockChart;
