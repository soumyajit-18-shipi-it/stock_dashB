import React from 'react';
import SearchBar from '../components/SearchBar';
import StockChart from '../components/StockChart';
import DataRangeSelector from '../components/DataRangeSelector';
import PredictionCard from '../components/PredictionCard';
import CompanyProfileCard from '../components/CompanyProfileCard';
import ErrorMessage from '../components/ErrorMessage';
import { useStock } from '../store/stock_store';
import { LayoutDashboard, BarChart3 } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { stockData, loading, error } = useStock();

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="w-8 h-8 text-blue-600" />
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
              Stock Intelligence
            </h1>
          </div>
          <SearchBar />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && <ErrorMessage message={error} />}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-500 font-medium">Analyzing market data...</p>
          </div>
        ) : stockData ? (
          <div className="space-y-6">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{stockData.profile.name} ({stockData.ticker})</h2>
                <p className="text-gray-500">{stockData.profile.sector} Sector</p>
              </div>
              <DataRangeSelector />
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Chart */}
              <div className="lg:col-span-2 space-y-6">
                <StockChart />
              </div>

              {/* Sidebar Components */}
              <div className="space-y-6">
                <PredictionCard />
                <CompanyProfileCard />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <BarChart3 className="w-16 h-16 text-gray-200 mb-4" />
            <h2 className="text-2xl font-bold text-gray-400">No stock analyzed yet</h2>
            <p className="text-gray-400 mt-2 max-w-md">
              Enter a stock ticker above to start transforming historical data into predictive insights.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
