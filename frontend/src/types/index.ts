export type Market = 'cn' | 'hk' | 'us';

export interface MarketMeta {
  id: Market;
  label: string;
  sub: string;
  count: number;
}

export interface HeadlineCard {
  code: string;
  name: string;
  pe: number | null;
  pep: number | null;
  pb: number | null;
  pbp: number | null;
  temperature: number | null;
}

export interface SectorItem {
  name: string;
  pe: number | null;
  pct: number | null;
}

export interface IndexRow {
  name: string;
  code: string;
  market: Market;
  sector: string | null;
  close: number | null;
  pe: number | null;
  pep: number | null;
  pb: number | null;
  pbp: number | null;
  temperature: number | null;
  sparkline: number[];
}

export interface IndexDetail extends IndexRow {
  // PE
  pe_min: number | null;
  pe_max: number | null;
  pe_avg: number | null;
  pe_dist: number[];
  pe_dist_min: number | null;
  pe_dist_max: number | null;
  // PB
  pb_min: number | null;
  pb_max: number | null;
  pb_avg: number | null;
  pb_dist: number[];
  pb_dist_min: number | null;
  pb_dist_max: number | null;
  // PS
  ps: number | null;
  psp: number | null;
  ps_min: number | null;
  ps_max: number | null;
  ps_avg: number | null;
  ps_dist: number[];
  ps_dist_min: number | null;
  ps_dist_max: number | null;
  // DYR
  dyr: number | null;
  dyrp: number | null;
  dyr_min: number | null;
  dyr_max: number | null;
  dyr_avg: number | null;
  dyr_dist: number[];
  dyr_dist_min: number | null;
  dyr_dist_max: number | null;
}

export interface RangeStats {
  p30: number | null;
  p50: number | null;
  p80: number | null;
  pct: number | null;   // 最新值在该区间的分位（0-100）
}

export interface IndexHistory {
  dates: string[];
  price: (number | null)[];
  pe:    (number | null)[];
  pb:    (number | null)[];
  ps:    (number | null)[];
  dyr:   (number | null)[];
  pe_stats:  RangeStats;
  pb_stats:  RangeStats;
  ps_stats:  RangeStats;
  dyr_stats: RangeStats;
}

export interface MarketOverview {
  market: Market;
  temperature: number | null;
  updated_at: string | null;
  headlines: HeadlineCard[];
  sectors: SectorItem[];
  series: Record<string, (number | null)[]>;
  series_dates: string[];
}
