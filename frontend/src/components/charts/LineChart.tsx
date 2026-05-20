export interface ReferenceLine {
  value: number;
  label?: string;
  color?: string;
  dashArray?: string;
}

interface Props {
  series: Record<string, (number | null)[]>;
  dates?: string[];
  referenceLines?: ReferenceLine[];
  width?: number;
  height?: number;
  palette?: string[];
  padding?: { l: number; r: number; t: number; b: number };
}

const DEFAULT_PADDING = { l: 44, r: 16, t: 16, b: 28 };

function buildPath(
  values: (number | null)[],
  xFn: (i: number) => number,
  yFn: (v: number) => number,
): string {
  let d = '';
  let moveTo = true;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v === null) { moveTo = true; continue; }
    d += ` ${moveTo ? 'M' : 'L'} ${xFn(i).toFixed(1)} ${yFn(v).toFixed(1)}`;
    moveTo = false;
  }
  return d.trim();
}

function computeYearTicks(dates: string[]): { yr: number; idx: number }[] {
  if (!dates.length) return [];
  const firstYear = parseInt(dates[0].slice(0, 4));
  const lastYear = parseInt(dates[dates.length - 1].slice(0, 4));
  const span = lastYear - firstYear;
  const step = span > 15 ? 4 : span > 8 ? 2 : 1;
  const result: { yr: number; idx: number }[] = [];
  for (let yr = Math.ceil((firstYear + 1) / step) * step; yr <= lastYear; yr += step) {
    const idx = dates.findIndex(d => d.startsWith(String(yr)));
    if (idx >= 0) result.push({ yr, idx });
  }
  return result;
}

export default function LineChart({
  series,
  dates,
  referenceLines,
  width = 720,
  height = 280,
  palette = ['#c66a1c', '#7d5fa6', '#3f7ec4', '#5fa180', '#4a5560'],
  padding = DEFAULT_PADDING,
}: Props) {
  const keys = Object.keys(series);
  const refVals = (referenceLines ?? []).map(r => r.value);
  const allVals = [...keys.flatMap(k => series[k]).filter((v): v is number => v !== null), ...refVals];
  const n = series[keys[0]]?.length ?? 0;
  if (n === 0 || allVals.length === 0) return null;

  const min = Math.min(...allVals);
  const max = Math.max(...allVals);
  const yPad = (max - min) * 0.08;
  const ymin = Math.max(0, min - yPad);
  const ymax = max + yPad;
  const W = width - padding.l - padding.r;
  const H = height - padding.t - padding.b;

  const x = (i: number) => padding.l + (i / (n - 1)) * W;
  const y = (v: number) => padding.t + (1 - (v - ymin) / (ymax - ymin)) * H;

  const yTicks = 4;
  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => ymin + (i / yTicks) * (ymax - ymin));
  const tickStep = (ymax - ymin) / yTicks;
  const yDecimals = tickStep >= 10 ? 0 : tickStep >= 1 ? 1 : tickStep >= 0.1 ? 2 : 3;
  const fmtTick = (v: number) => v.toFixed(yDecimals);

  const yearTicks = dates
    ? computeYearTicks(dates)
    : [2008, 2012, 2016, 2020, 2024].map(yr => ({
        yr,
        idx: Math.round(((yr - 2007) / (2026 - 2007)) * (n - 1)),
      }));

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={padding.l} x2={width - padding.r} y1={y(t)} y2={y(t)} stroke="var(--divider)" strokeWidth="1" />
          <text x={padding.l - 8} y={y(t) + 3} textAnchor="end" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{fmtTick(t)}</text>
        </g>
      ))}
      {yearTicks.map(({ yr, idx }) => (
        <text key={yr} x={x(idx)} y={height - 8} textAnchor="middle" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{yr}</text>
      ))}
      {keys.map((k, ki) => {
        const d = buildPath(series[k], x, y);
        return <path key={k} d={d} fill="none" stroke={palette[ki % palette.length]} strokeWidth="1.4" strokeLinejoin="round" strokeLinecap="round" opacity="0.9" />;
      })}
      {(referenceLines ?? []).map((rl, i) => {
        const yy = y(rl.value);
        const color = rl.color ?? 'var(--ink-3)';
        return (
          <g key={i}>
            <line
              x1={padding.l} x2={width - padding.r}
              y1={yy} y2={yy}
              stroke={color} strokeWidth="1"
              strokeDasharray={rl.dashArray ?? '4 3'}
              opacity="0.7"
            />
            {rl.label && (
              <text x={width - padding.r + 3} y={yy + 3} fontSize="9" fill={color} fontFamily="var(--font-mono)">{rl.label}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
