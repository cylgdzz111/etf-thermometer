import { useMarket } from '../../store/MarketContext';
import { useMarketOverview } from '../../api/market';
import LineChart from '../../components/charts/LineChart';
import PercentileChip from '../../components/charts/PercentileChip';
import { tempColor, tempLabel } from '../../utils/temperature';
import type { HeadlineCard, SectorItem } from '../../types';

const PALETTE = ['#c66a1c', '#7d5fa6', '#3f7ec4', '#5fa180', '#4a5560', '#b5505a'];

function HeadlineCardView({ d, color }: { d: HeadlineCard; color: string }) {
  return (
    <div className="stat">
      <div className="stat-label">
        <span className="swatch" style={{ background: color }} />
        {d.name}
      </div>
      <div className="stat-row">
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PE</div>
          <div className="stat-value">{d.pe != null ? d.pe.toFixed(2) : '—'}</div>
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PB</div>
          <div className="stat-value" style={{ fontSize: 18, color: 'var(--ink-1)' }}>
            {d.pb != null ? d.pb.toFixed(2) : '—'}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 2 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--ink-2)' }}>
          <span style={{ width: 24, color: 'var(--ink-3)' }}>PE</span>
          <PercentileChip p={d.pep} showLabel={false} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--ink-2)' }}>
          <span style={{ width: 24, color: 'var(--ink-3)' }}>PB</span>
          <PercentileChip p={d.pbp} showLabel={false} />
        </div>
      </div>
    </div>
  );
}

function SectorCell({ s }: { s: SectorItem }) {
  const pct = s.pct ?? 0;
  const bg = `color-mix(in oklch, ${tempColor(pct)} 22%, white)`;
  const border = `color-mix(in oklch, ${tempColor(pct)} 50%, var(--border))`;
  return (
    <div className="sector-cell" style={{ background: bg, boxShadow: `inset 0 0 0 1px ${border}` }}>
      <div className="name">{s.name}</div>
      <div>
        <div className="pct">
          {pct.toFixed(0)}
          <span style={{ fontSize: 11, color: 'var(--ink-2)', marginLeft: 2 }}>分位</span>
        </div>
        <div className="sub">PE {s.pe != null ? s.pe.toFixed(1) : '—'}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { market } = useMarket();
  const { data, isLoading, isError } = useMarketOverview(market);

  if (isLoading) {
    return (
      <div>
        <div className="page-head">
          <div>
            <h1 className="page-title">市场估值概览</h1>
          </div>
        </div>
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>
          加载中…
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div>
        <div className="page-head">
          <div>
            <h1 className="page-title">市场估值概览</h1>
          </div>
        </div>
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>
          数据加载失败，请稍后重试
        </div>
      </div>
    );
  }

  const temp = data.temperature;
  const seriesKeys = Object.keys(data.series);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1 className="page-title">市场估值概览</h1>
          <p className="page-sub">
            覆盖 A 股 · 港股 · 美股的核心宽基与行业指数。温度计读数综合 PE/PB 历史分位，
            为你提供「冷热」决策视角。
          </p>
        </div>
        <div className="page-meta">
          {data.updated_at && <span>更新至 {data.updated_at}</span>}
        </div>
      </div>

      {/* Market temperature summary + PE chart */}
      <div className="card" style={{ marginBottom: 20, padding: '22px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, gap: 24, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--ink-3)', marginBottom: 4, letterSpacing: '.04em', textTransform: 'uppercase' }}>当前市场温度</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span className="mono" style={{ fontSize: 42, fontWeight: 500, letterSpacing: '-0.02em', color: tempColor(temp) }}>
                {temp != null ? `${temp.toFixed(1)}°` : '—'}
              </span>
              {temp != null && (
                <span style={{ fontSize: 15, color: 'var(--ink-1)', fontWeight: 500 }}>{tempLabel(temp)}</span>
              )}
            </div>
          </div>
          {temp != null && (
            <div style={{ flex: 1, minWidth: 320, maxWidth: 520 }}>
              <div className="thermo-track" style={{ height: 10 }}>
                <div className="thermo-marker" style={{ left: `${temp}%`, width: 18, height: 18, borderWidth: 3 }} />
              </div>
              <div className="thermo-ticks">
                <span>极度低估</span><span>低估</span><span>偏低</span>
                <span>正常</span><span>偏高</span><span>高估</span><span>极度高估</span>
              </div>
            </div>
          )}
        </div>

        {/* PE series chart */}
        {seriesKeys.length > 0 && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>全市场 PE 走势</span>
              <div className="legend">
                {seriesKeys.map((k, i) => (
                  <span key={k} className="item">
                    <span className="sw" style={{ background: PALETTE[i % PALETTE.length] }} />
                    {k}
                  </span>
                ))}
              </div>
            </div>
            <div style={{ width: '100%', overflow: 'hidden' }}>
              <LineChart
                series={data.series}
                dates={data.series_dates}
                width={1340}
                height={300}
                palette={PALETTE}
              />
            </div>
          </>
        )}
      </div>

      {/* Headline cards */}
      {data.headlines.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(data.headlines.length, 6)}, 1fr)`, gap: 12, marginBottom: 20 }}>
          {data.headlines.map((d, i) => (
            <HeadlineCardView key={d.code} d={d} color={PALETTE[i % PALETTE.length]} />
          ))}
        </div>
      )}

      {/* Sector heatmap — 暂时隐藏 */}
    </div>
  );
}
