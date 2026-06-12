import { Building2, Globe, DollarSign, Activity, TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { CompanyProfile } from '../types';
import { formatCompactCurrency, formatCurrency } from '../utils/format';

interface CompanyProfileCardProps {
  profile: CompanyProfile;
}

export function CompanyProfileCard({ profile }: CompanyProfileCardProps) {
  const { t } = useTranslation();
  const currency = profile.currency || (profile.ticker.endsWith('.NS') ? 'INR' : 'USD');

  return (
    <div className="glass rounded-xl border border-slate-700 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">{profile.name || profile.ticker}</h2>
          <p className="text-slate-400 text-sm">{profile.ticker}</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/20 px-3 py-1 rounded-full">
          <Activity className="h-4 w-4 text-emerald-400" />
          <span className="text-emerald-400 text-sm font-medium">{t('companyLive')}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-slate-400 text-xs mb-1">{t('currentPrice')}</p>
          <p className="text-xl font-bold text-white">
            {profile.current_price ? formatCurrency(profile.current_price, currency) : t('notAvailable')}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-slate-400 text-xs mb-1">{t('previousClose')}</p>
          <p className="text-xl font-bold text-white">
            {profile.previous_close ? formatCurrency(profile.previous_close, currency) : t('notAvailable')}
          </p>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex items-center gap-3">
          <Building2 className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">{t('sector')}</span>{' '}
            <span className="text-white">{profile.sector || t('notAvailable')}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <TrendingUp className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">{t('industry')}</span>{' '}
            <span className="text-white">{profile.industry || t('notAvailable')}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <DollarSign className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">{t('marketCap')}</span>{' '}
            <span className="text-white">{profile.market_cap ? formatCompactCurrency(profile.market_cap, currency) : t('notAvailable')}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Globe className="h-4 w-4 text-slate-400" />
          <div>
            <span className="text-slate-400">{t('exchange')}</span>{' '}
            <span className="text-white">{profile.exchange || t('notAvailable')}</span>
            {profile.currency ? <span className="text-slate-400"> ({profile.currency})</span> : <span className="text-slate-400"> ({t('notAvailable')})</span>}
          </div>
        </div>
        {profile.country && (
          <div className="flex items-center gap-3">
            <Globe className="h-4 w-4 text-slate-400" />
            <div>
              <span className="text-slate-400">{t('country')}</span>{' '}
              <span className="text-white">{profile.country}</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700 grid grid-cols-2 gap-4">
        <div>
          <p className="text-slate-400 text-xs">{t('high52')}</p>
          <p className="text-emerald-400 font-semibold">
            {profile.week_52_high ? formatCurrency(profile.week_52_high, currency) : t('notAvailable')}
          </p>
        </div>
        <div>
          <p className="text-slate-400 text-xs">{t('low52')}</p>
          <p className="text-red-400 font-semibold">
            {profile.week_52_low ? formatCurrency(profile.week_52_low, currency) : t('notAvailable')}
          </p>
        </div>
      </div>
    </div>
  );
}
