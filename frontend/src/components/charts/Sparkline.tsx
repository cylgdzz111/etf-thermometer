interface Props {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  positive?: boolean;
}

export default function Sparkline({ data, width = 80, height = 22, color = 'var(--ink-2)', positive }: Props) {
  if (!data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const x = (i: number) => (i / (data.length - 1)) * width;
  const y = (v: number) => height - ((v - min) / (max - min || 1)) * (height - 2) - 1;
  const path = data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const last = data[data.length - 1];
  const first = data[0];
  const stroke = positive == null ? color : last > first ? 'var(--up)' : 'var(--down)';

  return (
    <svg width={width} height={height} className="spark">
      <path d={path} fill="none" stroke={stroke} strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(data.length - 1)} cy={y(last)} r="1.8" fill={stroke} />
    </svg>
  );
}
