import { tempColor } from '../../utils/temperature';

interface Props {
  p: number | null | undefined;
}

export default function PBar({ p }: Props) {
  if (p == null) return <span className="mono" style={{ color: 'var(--ink-3)' }}>—</span>;
  return (
    <div className="pbar">
      <div className="pbar-track">
        <div className="pbar-fill" style={{ width: `${p}%`, background: tempColor(p) }} />
      </div>
      <span className="mono" style={{ fontSize: 11, color: 'var(--ink-2)' }}>{p.toFixed(0)}%</span>
    </div>
  );
}
