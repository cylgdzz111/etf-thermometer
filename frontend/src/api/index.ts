import { useQuery } from '@tanstack/react-query';
import type { Market, IndexRow, IndexDetail, IndexHistory } from '../types';
import client from './client';

interface IndexListParams {
  market: Market;
  sector?: string;
  q?: string;
}

export function useIndexList(params: IndexListParams) {
  return useQuery({
    queryKey: ['index-list', params],
    queryFn: () =>
      client.get<{ data: IndexRow[] }>('/indices', { params }).then(r => r.data.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useIndexDetail(code: string) {
  return useQuery({
    queryKey: ['index-detail', code],
    queryFn: () =>
      client.get<{ data: IndexDetail }>(`/indices/${code}`).then(r => r.data.data),
    staleTime: 5 * 60 * 1000,
    enabled: !!code,
  });
}

export function useIndexHistory(code: string, range: '1y' | '3y' | '5y' | '10y' | 'all') {
  return useQuery({
    queryKey: ['index-history', code, range],
    queryFn: () =>
      client
        .get<{ data: IndexHistory }>(`/indices/${code}/history`, { params: { range } })
        .then(r => r.data.data),
    staleTime: 10 * 60 * 1000,
    enabled: !!code,
  });
}
