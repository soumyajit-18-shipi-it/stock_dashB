import { Building2, Globe, DollarSign, Activity, TrendingUp } from 'lucide-react';
import type { CompanyProfile } from '../types';

interface CompanyProfileCardProps {
  profile: CompanyProfile;
}

function formatMarketCap(value?: number): string {
  if (!value) return 'Not Available';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

export function CompanyProfileCard({ profile }: CompanyProfileCardProps) {
  return (
    <div className="glass rounded-xl border border-slate-700 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">{profile.name || profile.ticker}</h2>
          <p className="text-slate-400 text-sm">{profile.ticker}</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/20 px-3 py-1 rounded-full">
          <Activity className="h-4 w-4 text-emerald-400" />
          <span className="text-emerald-400 text-sm font-medium">Live</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-slate-400 text-xs mb-1">Current Price</p>
          <p className="text-xl font-bold text-white">
            {profile.current_price ? `$${profile.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'Not Available'}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-slate-400 text-xs mb-1">Previous Close</p>
          <p className="text-xl font-bold text-white">
            {profile.previous_close ? `$${profile.previous_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'Not Available'}
          </p>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex items-center gap-3">
          <Building2 className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">Sector:</span>{' '}
            <span className="text-white">{profile.sector || 'Not Available'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <TrendingUp className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">Industry:</span>{' '}
            <span className="text-white">{profile.industry || 'Not Available'}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <DollarSign className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">Market Cap:</span>{' '}
            <span className="text-white">{formatMarketCap(profile.market_cap)}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Globe className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">Exchange:</span>{' '}
            <span className="text-white">{profile.exchange || 'Not Available'}</span>
            {profile.currency ? <span className="text-slate-400"> ({profile.currency})</span> : <span className="text-slate-400"> (Not Available)</span>}
          </div>
        </div>
        {profile.country && (
          <div className="flex items-center gap-3">
            <Globe className="h-4 w-4 text-slate-400" />
            <div>
              <span className="text-slate-400">Country:</span>{' '}
              <span className="text-white">{profile.country}</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700 grid grid-cols-2 gap-4">
        <div>
          <p className="text-slate-400 text-xs">52W High</p>
          <p className="text-emerald-400 font-semibold">
            {profile.week_52_high ? `$${profile.week_52_high.toFixed(2)}` : 'Not Available'}
          </p>
        </div>
        <div>
          <p className="text-slate-400 text-xs">52W Low</p>
          <p className="text-red-400 font-semibold">
            {profile.week_52_low ? `$${profile.week_52_low.toFixed(2)}` : 'Not Available'}
          </p>
        </div>
      </div>
    </div>
  );
}
