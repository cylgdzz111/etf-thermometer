export type Market = 'cn' | 'hk' | 'us';

export interface MarketMeta {
  id: Market;
  label: string;
  sub: string;
  count: number;
}

export interface HeadlineCard {
  name: string;
  pe: number;
  pep: number;
  pb: number;
  pbp: number;
}

export interface SectorItem {
  name: string;
  pe: number;
  pct: number;
  chg: number;
}

export interface IndexRow {
  name: string;
  code: string;
  market: Market;
  sector: string;
  close: number;
  chg: number;
  w52: number;
  peakDist: number;
  pe: number;
  pep: number;
  pb: number;
  pbp: number;
  fav: boolean;
}

export interface IndexDetail extends IndexRow {
  pe_min: number;
  pe_max: number;
  pe_avg: number;
  pb_min: number;
  pb_max: number;
  pb_avg: number;
  total_ret: number;
  drawdown: number;
  price_series: number[];
  pe_series: number[];
  pe_dist: number[];
  pb_dist: number[];
}

export interface MarketOverview {
  market: Market;
  temperature: number;
  updated_at: string;
  headlines: HeadlineCard[];
  sectors: SectorItem[];
  series: Record<string, number[]>;
}
