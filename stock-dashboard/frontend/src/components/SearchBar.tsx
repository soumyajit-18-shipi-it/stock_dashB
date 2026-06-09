import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { useStock } from '../store/stock_store';
import { fetchStockData } from '../services/api_client';

const SearchBar: React.FC = () => {
  const [input, setInput] = useState('');
  const { 
    setStockData, 
    setLoading, 
    setError, 
    setCurrentTicker, 
    currentRange, 
    currentModel 
  } = useStock();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError(null);
    setCurrentTicker(input.trim().toUpperCase());

    try {
      const data = await fetchStockData(input.trim(), currentRange, currentModel);
      setStockData(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching data');
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSearch} className="flex w-full max-w-md gap-2">
      <div className="relative flex-1">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Search className="w-5 h-5 text-gray-400" />
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter stock ticker (e.g. AAPL, TSLA)"
          className="block w-full p-3 pl-10 text-sm border border-gray-300 rounded-lg bg-white focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <button
        type="submit"
        className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium text-sm transition-colors"
      >
        Analyze
      </button>
    </form>
  );
};

export default SearchBar;
