export type DateRange = '1m' | '6m' | '1y' | '5y';
export type ModelType = 'linear' | 'rf';
export type TrendDirection = 'increase' | 'decrease';

// Re-export shared contract types
import type { CompanyProfile, StockPricePoint } from '../shared/stockContract';
export type { CompanyProfile, StockPricePoint };

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
  company_name?: string;
  created_at?: string;
}

export interface SearchHistoryItem {
  id?: string;
  query?: string;
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

export interface FeedbackIssue {
  id: string;
  user_id?: string;
  email?: string;
  category: string;
  title: string;
  description: string;
  page_url?: string;
  screenshot_url?: string;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
}

export interface AdminStats {
  total_users: number;
  new_users_today: number;
  new_users_this_week: number;
  total_feedback_issues: number;
  open_feedback_issues: number;
  last_updated: string;
}
