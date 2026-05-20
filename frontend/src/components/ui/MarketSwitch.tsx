import type { Market } from '../../types';

const MARKETS: { id: Market; label: string; sub: string }[] = [
  { id: 'cn', label: 'A 股', sub: 'CN' },
  { id: 'hk', label: '港股', sub: 'HK' },
  { id: 'us', label: '美股', sub: 'US' },
];

interface Props {
  value: Market;
  onChange: (m: Market) => void;
}

export default function MarketSwitch({ value, onChange }: Props) {
  return (
    <div className="market-switch">
      {MARKETS.map(m => (
        <button key={m.id} className={value === m.id ? 'on' : ''} onClick={() => onChange(m.id)}>
          {m.label}
          <span style={{ opacity: 0.55, fontSize: 10.5, fontFamily: 'var(--font-mono)', marginLeft: 2 }}>{m.sub}</span>
        </button>
      ))}
    </div>
  );
}
