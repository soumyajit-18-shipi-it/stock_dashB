import React, { createContext, useContext, useState, ReactNode } from 'react';
import { StockResponse } from '../services/api_client';

interface StockContextType {
  stockData: StockResponse | null;
  setStockData: (data: StockResponse | null) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  currentTicker: string;
  setCurrentTicker: (ticker: string) => void;
  currentRange: string;
  setCurrentRange: (range: string) => void;
  currentModel: string;
  setCurrentModel: (model: string) => void;
}

const StockContext = createContext<StockContextType | undefined>(undefined);

export const StockProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [stockData, setStockData] = useState<StockResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTicker, setCurrentTicker] = useState('');
  const [currentRange, setCurrentRange] = useState('1y');
  const [currentModel, setCurrentModel] = useState('linear');

  return (
    <StockContext.Provider
      value={{
        stockData,
        setStockData,
        loading,
        setLoading,
        error,
        setError,
        currentTicker,
        setCurrentTicker,
        currentRange,
        setCurrentRange,
        currentModel,
        setCurrentModel,
      }}
    >
      {children}
    </StockContext.Provider>
  );
};

export const useStock = () => {
  const context = useContext(StockContext);
  if (context === undefined) {
    throw new Error('useStock must be used within a StockProvider');
  }
  return context;
};
