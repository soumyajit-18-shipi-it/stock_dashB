import type { StockResponse } from '../types';

export function currencyForStock(stock?: StockResponse | null): string {
  const currency = stock?.profile.currency?.toUpperCase();
  if (currency) return currency;
  return stock?.profile.ticker?.endsWith('.NS') ? 'INR' : 'USD';
}

export function formatCurrency(value?: number | null, currency = 'USD'): string {
  if (value == null || Number.isNaN(value)) return 'Not Available';
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCompactCurrency(value?: number | null, currency = 'USD'): string {
  if (value == null || Number.isNaN(value)) return 'Not Available';
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(value);
}
