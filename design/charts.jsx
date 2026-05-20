// Chart primitives — pure SVG, no deps
const { useState, useMemo, useRef, useEffect } = React;

function LineChart({ series, width = 720, height = 280, palette, labels, padding = { l: 36, r: 16, t: 16, b: 28 }, showAxis = true }) {
  const keys = Object.keys(series);
  const all = keys.flatMap(k => series[k]);
  const n = series[keys[0]].length;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const yPad = (max - min) * 0.08;
  const ymin = Math.max(0, min - yPad);
  const ymax = max + yPad;

  const W = width - padding.l - padding.r;
  const H = height - padding.t - padding.b;

  const x = i => padding.l + (i / (n - 1)) * W;
  const y = v => padding.t + (1 - (v - ymin) / (ymax - ymin)) * H;

  const yTicks = 4;
  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => ymin + (i / yTicks) * (ymax - ymin));

  const yearStart = 2007;
  const yearEnd = 2026;
  const yearTicks = [2008, 2012, 2016, 2020, 2024];

  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {showAxis && ticks.map((t, i) => (
        <g key={i}>
          <line x1={padding.l} x2={width - padding.r} y1={y(t)} y2={y(t)} stroke="var(--divider)" strokeWidth="1" />
          <text x={padding.l - 8} y={y(t) + 3} textAnchor="end" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{Math.round(t)}</text>
        </g>
      ))}
      {showAxis && yearTicks.map(yr => {
        const i = ((yr - yearStart) / (yearEnd - yearStart)) * (n - 1);
        return <text key={yr} x={x(i)} y={height - 8} textAnchor="middle" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-mono)">{yr}</text>;
      })}
      {keys.map((k, ki) => {
        const path = series[k].map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
        return <path key={k} d={path} fill="none" stroke={palette[ki % palette.length]} strokeWidth="1.4" strokeLinejoin="round" strokeLinecap="round" opacity="0.9" />;
      })}
    </svg>
  );
}

function Sparkline({ data, width = 80, height = 22, color = 'var(--ink-2)', positive }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const x = i => (i / (data.length - 1)) * width;
  const y = v => height - ((v - min) / (max - min || 1)) * (height - 2) - 1;
  const path = data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const last = data[data.length - 1];
  const first = data[0];
  const stroke = positive == null ? color : (last > first ? 'var(--up)' : 'var(--down)');
  return (
    <svg width={width} height={height} className="spark">
      <path d={path} fill="none" stroke={stroke} strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(data.length - 1)} cy={y(last)} r="1.8" fill={stroke} />
    </svg>
  );
}

function ThermoBar({ percentile, width = 220 }) {
  const p = Math.max(0, Math.min(100, percentile ?? 0));
  return (
    <div className="thermometer" style={{ width }}>
      <div className="thermo-track">
        <div className="thermo-marker" style={{ left: `${p}%` }} />
      </div>
    </div>
  );
}

function PercentileChip({ p, showLabel = true }) {
  if (p == null) return <span className="mono" style={{ color: 'var(--ink-3)' }}>—</span>;
  const bg = `color-mix(in oklch, ${tempColor(p)} 18%, white)`;
  const fg = `color-mix(in oklch, ${tempColor(p)} 70%, var(--ink))`;
  return (
    <span className="percentile" style={{ background: bg, color: fg }}>
      <span className="dot" style={{ background: tempColor(p) }} />
      {p.toFixed(1)}%{showLabel && <span style={{ opacity: .7, marginLeft: 2 }}>· {tempLabel(p)}</span>}
    </span>
  );
}

function PBar({ p }) {
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

function DistributionChart({ data, current, width = 360, height = 100 }) {
  const max = Math.max(...data);
  const w = width / data.length;
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {data.map((v, i) => {
        const h = (v / max) * (height - 12);
        const isCurrent = i === current;
        return (
          <rect key={i}
            x={i * w + 1}
            y={height - h}
            width={w - 2}
            height={h}
            fill={isCurrent ? 'var(--temp-5)' : `color-mix(in oklch, var(--temp-4) ${30 + (v/max)*40}%, white)`}
            rx="1.5"
          />
        );
      })}
      <line x1="0" x2={width} y1={height - 1} y2={height - 1} stroke="var(--accent)" strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
    </svg>
  );
}

window.Charts = { LineChart, Sparkline, ThermoBar, PercentileChip, PBar, DistributionChart };
