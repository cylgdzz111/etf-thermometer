interface Props {
  series: Record<string, number[]>;
  width?: number;
  height?: number;
  palette?: string[];
  padding?: { l: number; r: number; t: number; b: number };
}

const DEFAULT_PADDING = { l: 36, r: 16, t: 16, b: 28 };

export default function LineChart({
  series,
  width = 720,
  height = 280,
  palette = ['#c66a1c', '#7d5fa6', '#3f7ec4', '#5fa180', '#4a5560'],
  padding = DEFAULT_PADDING,
}: Props) {
  const keys = Object.keys(series);
  const all = keys.flatMap(k => series[k]);
  const n = series[keys[0]]?.length ?? 0;
  if (n === 0) return null;

  const min = Math.min(...all);
  const max = Math.max(...all);
  const yPad = (max - min) * 0.08;
  const ymin = Math.max(0, min - yPad);
  const ymax = max + yPad;
  const W = width - padding.l - padding.r;
  const H = height - padding.t - padding.b;

  const x = (i: number) => padding.l + (i / (n - 1)) * W;
  const y = (v: number) => padding.t + (1 - (v - ymin) / (ymax - ymin)) * H;

  const yTicks = 4;
  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => ymin + (i / yTicks) * (ymax - ymin));
  const yearTicks = [2008, 2012, 2016, 2020, 2024];
  const yearStart = 2007, yearEnd = 2026;

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={padding.l} x2={width - padding.r} y1={y(t)} y2={y(t)} stroke="var(--divider)" strokeWidth="1" />
          <text x={padding.l - 8} y={y(t) + 3} textAnchor="end" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{Math.round(t)}</text>
        </g>
      ))}
      {yearTicks.map(yr => {
        const i = ((yr - yearStart) / (yearEnd - yearStart)) * (n - 1);
        return (
          <text key={yr} x={x(i)} y={height - 8} textAnchor="middle" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{yr}</text>
        );
      })}
      {keys.map((k, ki) => {
        const d = series[k].map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
        return <path key={k} d={d} fill="none" stroke={palette[ki % palette.length]} strokeWidth="1.4" strokeLinejoin="round" strokeLinecap="round" opacity="0.9" />;
      })}
    </svg>
  );
}
