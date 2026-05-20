import { tempColor, tempLabel } from '../../utils/temperature';

interface Props {
  p: number | null | undefined;
  showLabel?: boolean;
}

export default function PercentileChip({ p, showLabel = true }: Props) {
  if (p == null) return <span className="mono" style={{ color: 'var(--ink-3)' }}>—</span>;
  const bg = `color-mix(in oklch, ${tempColor(p)} 18%, white)`;
  const fg = `color-mix(in oklch, ${tempColor(p)} 70%, var(--ink))`;
  return (
    <span className="percentile" style={{ background: bg, color: fg }}>
      <span className="dot" style={{ background: tempColor(p) }} />
      {p.toFixed(1)}%
      {showLabel && <span style={{ opacity: 0.7, marginLeft: 2 }}>· {tempLabel(p)}</span>}
    </span>
  );
}
