const TEMP_COLORS = [
  'var(--temp-0)',
  'var(--temp-1)',
  'var(--temp-2)',
  'var(--temp-3)',
  'var(--temp-4)',
  'var(--temp-5)',
  'var(--temp-6)',
] as const;

export function tempColor(p: number | null | undefined): string {
  if (p == null) return 'var(--ink-4)';
  if (p < 15) return TEMP_COLORS[0];
  if (p < 30) return TEMP_COLORS[1];
  if (p < 45) return TEMP_COLORS[2];
  if (p < 60) return TEMP_COLORS[3];
  if (p < 75) return TEMP_COLORS[4];
  if (p < 90) return TEMP_COLORS[5];
  return TEMP_COLORS[6];
}

export function tempLabel(p: number | null | undefined): string {
  if (p == null) return '—';
  if (p < 15) return '极度低估';
  if (p < 30) return '低估';
  if (p < 45) return '偏低';
  if (p < 60) return '正常';
  if (p < 75) return '偏高';
  if (p < 90) return '高估';
  return '极度高估';
}
