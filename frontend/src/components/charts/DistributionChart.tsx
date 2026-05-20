interface Props {
  data: number[];
  current?: number;
  width?: number;
  height?: number;
}

export default function DistributionChart({ data, current, width = 360, height = 100 }: Props) {
  if (!data.length) return null;
  const max = Math.max(...data);
  const w = width / data.length;

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {data.map((v, i) => {
        const h = (v / max) * (height - 12);
        const isCurrent = i === current;
        return (
          <rect
            key={i}
            x={i * w + 1}
            y={height - h}
            width={w - 2}
            height={h}
            fill={isCurrent ? 'var(--temp-5)' : `color-mix(in oklch, var(--temp-4) ${30 + (v / max) * 40}%, white)`}
            rx="1.5"
          />
        );
      })}
      <line x1="0" x2={width} y1={height - 1} y2={height - 1} stroke="var(--accent)" strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
    </svg>
  );
}
