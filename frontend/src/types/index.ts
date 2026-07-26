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
  submitter_name?: string;
  submitter_avatar_url?: string;
  submitter_provider?: string;
}

export interface AdminUserSummary {
  id: string;
  email?: string;
  full_name?: string;
  avatar_url?: string;
  provider?: string;
  first_seen_at?: string;
  last_seen_at?: string;
  total_feedback_count?: number;
  total_watchlist_items?: number;
  total_searches?: number;
}

export interface AdminStats {
  total_users: number;
  new_users_today: number;
  new_users_this_week: number;
  active_today: number;
  total_feedback_issues: number;
  open_feedback_issues: number;
  latest_signups: AdminUserSummary[];
  recent_feedback: FeedbackIssue[];
  users: AdminUserSummary[];
  last_updated: string;
}

export type RiskTolerance = 'conservative' | 'balanced' | 'aggressive';
export type InvestmentHorizon = 'short' | 'medium' | 'long';

export interface ComponentScore {
  score: number;
  confidence: number;
  reason: string;
  evidence: string[];
  metrics: Record<string, unknown>;
  weight: number;
  contribution: number;
}

export interface ExplanationFeature {
  feature: string;
  display_name: string;
  value: number;
  contribution: number;
  direction: 'positive' | 'negative';
  importance_percent: number;
}

export interface PredictionExplanation {
  ticker: string;
  model: string;
  method: string;
  provider_status: string;
  base_value: number;
  predicted_price: number;
  current_price: number;
  expected_return: number;
  confidence: number;
  uncertainty_lower: number;
  uncertainty_upper: number;
  features: ExplanationFeature[];
  additivity_residual: number;
}

export interface RecommendationResponse {
  ticker: string;
  generated_at: string;
  risk_tolerance: RiskTolerance;
  decision: {
    recommendation: 'BUY' | 'HOLD' | 'SELL';
    overall_score: number;
    confidence: number;
    strengths: string[];
    weaknesses: string[];
    risk_level: 'low' | 'medium' | 'high';
    expected_return: number;
    expected_downside: number;
    investment_horizon: string;
    components: Record<string, ComponentScore>;
    policy_checks: Record<string, boolean>;
  };
  prediction_explanation: PredictionExplanation | null;
}

export interface PortfolioHoldingInput {
  ticker: string;
  quantity?: number;
  average_cost?: number;
  weight?: number;
}

export interface PortfolioHoldingSnapshot {
  ticker: string;
  quantity: number | null;
  average_cost: number | null;
  current_price: number;
  market_value: number;
  weight: number;
  annual_return: number;
  annual_volatility: number;
  risk_contribution: number;
  sector: string;
  country: string;
  market_cap_bucket: string;
  holding_score: number;
}

export interface PortfolioAnalysis {
  generated_at: string;
  metrics: {
    portfolio_score: number;
    diversification_score: number;
    risk_score: number;
    expected_return: number;
    expected_volatility: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    maximum_drawdown: number;
    value_at_risk_95: number;
    beta: number | null;
    effective_holdings: number;
    concentration_hhi: number;
  };
  holdings: PortfolioHoldingSnapshot[];
  sector_exposure: Record<string, number>;
  country_exposure: Record<string, number>;
  market_cap_exposure: Record<string, number>;
  factor_exposure: Record<string, number>;
  correlation_matrix: {
    tickers: string[];
    values: number[][];
  };
  efficient_frontier: Array<{
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    weights: Record<string, number>;
  }>;
  monte_carlo: {
    simulations: number;
    horizon_days: number;
    expected_terminal_value: number;
    percentile_5: number;
    percentile_50: number;
    percentile_95: number;
    loss_probability: number;
  };
  rebalancing: Array<{
    ticker: string;
    current_weight: number;
    target_weight: number;
    change: number;
    action: 'INCREASE' | 'REDUCE' | 'HOLD';
  }>;
  allocation_timeline: Array<{
    date: string;
    weights: Record<string, number>;
  }>;
  largest_risks: string[];
  weakest_holdings: string[];
  best_holdings: string[];
  explanation: string[];
  data_warnings: string[];
}

export interface SavedPortfolio {
  id: string;
  user_id: string;
  name: string;
  analysis_snapshot?: PortfolioAnalysis | null;
  holdings?: PortfolioHoldingInput[];
  created_at?: string;
  updated_at?: string;
}
