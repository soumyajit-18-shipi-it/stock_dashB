export interface CompanyProfile {
  ticker: string;
  name: string;

  sector: string | null;
  industry: string | null;

  market_cap: number | null;

  current_price: number | null;
  previous_close: number | null;

  exchange: string | null;
  country: string | null;

  currency: string | null;

  week_52_high: number | null;
  week_52_low: number | null;

  logo?: string | null;
  website?: string | null;
}

export interface StockPrediction {
  predicted_price: number;
  trend: "increase" | "decrease";
  confidence: number;
  model_used: string;
}

export interface StockResponse {
  ticker: string;
  profile: CompanyProfile;
  prediction: StockPrediction;
  confidence: number;
}
