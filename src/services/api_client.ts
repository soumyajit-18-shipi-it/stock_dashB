import { createClient } from '@supabase/supabase-js';
import type { DateRange, ModelType, StockResponse, WatchlistItem, SearchHistoryItem, PredictionRecord } from '../types';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://buvchebubpanpzoxlvwi.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1dmNoZWJ1YnBhbnB6b3hsdndpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwNTkyNzgsImV4cCI6MjA5NjYzNTI3OH0.uVSvcipXUpRaDwnjvtd_bnOcloWs0zsV-0kXDsFZv_c';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const api = {
  async getStock(ticker: string, range: DateRange, model: ModelType): Promise<StockResponse> {
    const { data, error } = await supabase.functions.invoke('stock-analysis', {
      body: undefined,
      headers: {
        'ticker': ticker,
        'range': range,
        'model': model,
      },
    });

    if (error) {
      throw new Error(error.message || 'Failed to fetch stock data');
    }

    return data as StockResponse;
  },

  async getWatchlist(): Promise<WatchlistItem[]> {
    const { data, error } = await supabase
      .from('watchlists')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  },

  async addToWatchlist(ticker: string, name?: string): Promise<WatchlistItem> {
    const { data, error } = await supabase
      .from('watchlists')
      .insert({ ticker, name })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async removeFromWatchlist(id: string): Promise<void> {
    const { error } = await supabase
      .from('watchlists')
      .delete()
      .eq('id', id);

    if (error) throw error;
  },

  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    const { data, error } = await supabase
      .from('search_history')
      .select('*')
      .order('searched_at', { ascending: false })
      .limit(50);

    if (error) throw error;
    return data || [];
  },

  async addSearchHistory(ticker: string): Promise<SearchHistoryItem> {
    const { data, error } = await supabase
      .from('search_history')
      .insert({ ticker })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async clearSearchHistory(): Promise<void> {
    const { error } = await supabase
      .from('search_history')
      .delete()
      .neq('id', '00000000-0000-0000-0000-000000000000');

    if (error) throw error;
  },

  async getPredictions(ticker?: string): Promise<PredictionRecord[]> {
    let query = supabase
      .from('predictions')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(100);

    if (ticker) {
      query = query.eq('ticker', ticker);
    }

    const { data, error } = await query;
    if (error) throw error;
    return data || [];
  },

  async savePrediction(prediction: PredictionRecord): Promise<PredictionRecord> {
    const { data, error } = await supabase
      .from('predictions')
      .insert({
        ticker: prediction.ticker,
        model: prediction.model,
        predicted_price: prediction.predicted_price,
        actual_price: prediction.actual_price,
        confidence: prediction.confidence,
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async healthCheck(): Promise<{ status: string }> {
    return { status: 'healthy' };
  },
};
