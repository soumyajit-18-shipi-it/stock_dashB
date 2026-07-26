import { useQuery } from '@tanstack/react-query';

import { api } from '../services/api_client';

import type {
  DateRange,
  InvestmentHorizon,
  ModelType,
  RiskTolerance,
} from '../types';

export function useRecommendation(
  ticker: string,
  range: DateRange,
  model: ModelType,
  riskTolerance: RiskTolerance,
  horizon: InvestmentHorizon
) {
  return useQuery({
    queryKey: ['recommendation', ticker, range, model, riskTolerance, horizon],
    queryFn: () =>
      api.getRecommendation(ticker, range, model, riskTolerance, horizon),
    enabled: Boolean(ticker),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
