export type DateRange = '1m' | '6m' | '1y' | '5y';
export type ModelType = 'linear' | 'rf';
export type TrendDirection = 'increase' | 'decrease';

export interface StockPricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma7?: number;
  ma21?: number;
}

export interface CompanyProfile {
  ticker: string;
  name?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  current_price?: number;
  previous_close?: number;
  currency?: string;
  exchange?: string;
  country?: string;
  week_52_high?: number;
  week_52_low?: number;
}

export interface PredictionResult {
  predicted_price: number;
  trend: TrendDirection;
  confidence: number;
  model_used: string;
}

export interface ModelMetrics {
  rmse: number;
  mae: number;
  r2: number;
}

export interface StockResponse {
  ticker: string;
  profile: CompanyProfile;
  history: StockPricePoint[];
  prediction: PredictionResult;
  metrics: ModelMetrics;
  confidence: number;
}

export interface WatchlistItem {
  id?: string;
  ticker: string;
  name?: string;
  created_at?: string;
}

export interface SearchHistoryItem {
  id?: string;
  ticker: string;
  searched_at?: string;
}

export interface PredictionRecord {
  id?: string;
  ticker: string;
  model: string;
  predicted_price: number;
  actual_price?: number;
  confidence: number;
  created_at?: string;
}

export interface AppState {
  ticker: string;
  dateRange: DateRange;
  model: ModelType;
  stockData: StockResponse | null;
  watchlist: WatchlistItem[];
  searchHistory: SearchHistoryItem[];
  predictions: PredictionRecord[];
  isLoading: boolean;
  error: string | null;
  setTicker: (ticker: string) => void;
  setDateRange: (range: DateRange) => void;
  setModel: (model: ModelType) => void;
  setStockData: (data: StockResponse | null) => void;
  setWatchlist: (items: WatchlistItem[]) => void;
  addToWatchlist: (item: WatchlistItem) => void;
  removeFromWatchlist: (id: string) => void;
  setSearchHistory: (items: SearchHistoryItem[]) => void;
  setPredictions: (items: PredictionRecord[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}
