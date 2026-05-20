import { useQuery } from '@tanstack/react-query';
import type { Market, MarketOverview } from '../types';
import client from './client';

export function useMarketOverview(market: Market) {
  return useQuery({
    queryKey: ['market-overview', market],
    queryFn: () =>
      client.get<{ data: MarketOverview }>(`/market/${market}/overview`).then(r => r.data.data),
    staleTime: 5 * 60 * 1000,
  });
}
