const BASE_URL = 'http://localhost:8000/api/v1';

export interface StockResponse {
  ticker: string;
  profile: {
    name: string;
    sector: string;
    market_cap: number;
    high_52w: number;
    low_52w: number;
  };
  history: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma7?: number;
    ma21?: number;
  }>;
  prediction: {
    model: string;
    predicted_price: number;
    trend: 'increase' | 'decrease';
    current_price: number;
  };
}

export const fetchStockData = async (
  ticker: string,
  range: string = '1y',
  model: string = 'linear'
): Promise<StockResponse> => {
  const response = await fetch(
    `${BASE_URL}/stock/${ticker}?range=${range}&model=${model}`
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to fetch stock data');
  }

  return response.json();
};

export const checkHealth = async (): Promise<{ status: string }> => {
  const response = await fetch(`${BASE_URL}/health`);
  return response.json();
};
