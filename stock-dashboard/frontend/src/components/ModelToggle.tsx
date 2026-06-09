import React from 'react';
import { useStock } from '../store/stock_store';
import { fetchStockData } from '../services/api_client';

const models = [
  { label: 'Linear Regression', value: 'linear' },
  { label: 'Random Forest', value: 'rf' },
];

const ModelToggle: React.FC = () => {
  const { 
    currentModel, 
    setCurrentModel, 
    currentTicker, 
    currentRange, 
    setStockData, 
    setLoading, 
    setError 
  } = useStock();

  const handleModelChange = async (model: string) => {
    setCurrentModel(model);
    if (!currentTicker) return;

    setLoading(true);
    try {
      const data = await fetchStockData(currentTicker, currentRange, model);
      setStockData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to update prediction model');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex bg-gray-100 p-1 rounded-lg">
      {models.map((m) => (
        <button
          key={m.value}
          onClick={() => handleModelChange(m.value)}
          className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
            currentModel === m.value
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
};

export default ModelToggle;
