import React from 'react';
import { Info, Globe, Building2, Wallet } from 'lucide-react';
import { useStock } from '../store/stock_store';

const CompanyProfileCard: React.FC = () => {
  const { stockData } = useStock();

  if (!stockData) return null;

  const { profile } = stockData;

  const formatCurrency = (val: number) => {
    if (val >= 1e12) return `${(val / 1e12).toFixed(2)}T`;
    if (val >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `${(val / 1e6).toFixed(2)}M`;
    return val.toLocaleString();
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-6">
        <Info className="w-5 h-5 text-blue-600" />
        <h3 className="font-bold text-gray-800">Company Profile</h3>
      </div>

      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <Building2 className="w-4 h-4 text-gray-400 mt-1" />
          <div>
            <p className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Sector</p>
            <p className="text-sm font-semibold text-gray-700">{profile.sector}</p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Wallet className="w-4 h-4 text-gray-400 mt-1" />
          <div>
            <p className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Market Cap</p>
            <p className="text-sm font-semibold text-gray-700">${formatCurrency(profile.market_cap)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-50">
          <div>
            <p className="text-[10px] text-gray-400 uppercase font-bold tracking-wider mb-1">52W High</p>
            <p className="text-sm font-bold text-green-600">${profile.high_52w.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-[10px] text-gray-400 uppercase font-bold tracking-wider mb-1">52W Low</p>
            <p className="text-sm font-bold text-red-600">${profile.low_52w.toLocaleString()}</p>
          </div>
        </div>

        <div className="pt-4">
          <div className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-xs font-medium cursor-pointer">
            <Globe className="w-3 h-3" />
            <span>Visit Company Website</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyProfileCard;
