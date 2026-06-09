import React from 'react';
import { useStock } from '../store/stock_store';
import { fetchStockData } from '../services/api_client';

const ranges = [
  { label: '1 Month', value: '1m' },
  { label: '6 Months', value: '6m' },
  { label: '1 Year', value: '1y' },
  { label: '5 Years', value: '5y' },
];

const DataRangeSelector: React.FC = () => {
  const { 
    currentRange, 
    setCurrentRange, 
    currentTicker, 
    currentModel, 
    setStockData, 
    setLoading, 
    setError 
  } = useStock();

  const handleRangeChange = async (range: string) => {
    setCurrentRange(range);
    if (!currentTicker) return;

    setLoading(true);
    try {
      const data = await fetchStockData(currentTicker, range, currentModel);
      setStockData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to update data range');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex bg-gray-100 p-1 rounded-lg">
      {ranges.map((r) => (
        <button
          key={r.value}
          onClick={() => handleRangeChange(r.value)}
          className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
            currentRange === r.value
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
};

export default DataRangeSelector;
