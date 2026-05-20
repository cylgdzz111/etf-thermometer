// Dashboard view — 市场估值概览
const { useState: useState_d, useMemo: useMemo_d } = React;
const { LineChart: LC, Sparkline: SP, ThermoBar: TH, PercentileChip: PC } = window.Charts;

const PALETTE = [
  '#c66a1c', // accent
  '#7d5fa6', // muted purple
  '#3f7ec4', // dust blue
  '#5fa180', // sage
  '#4a5560', // slate
];

function HeadlineCard({ d, palette }) {
  return (
    <div className="stat">
      <div className="stat-label">
        <span className="swatch" style={{ background: palette }} />
        {d.name}
      </div>
      <div className="stat-row">
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PE</div>
          <div className="stat-value">{d.pe.toFixed(2)}</div>
        </div>
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PB</div>
          <div className="stat-value" style={{ fontSize: 18, color: 'var(--ink-1)' }}>{d.pb.toFixed(2)}</div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 2 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--ink-2)' }}>
          <span style={{ width: 24, color: 'var(--ink-3)' }}>PE</span>
          <PC p={d.pep} showLabel={false} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--ink-2)' }}>
          <span style={{ width: 24, color: 'var(--ink-3)' }}>PB</span>
          <PC p={d.pbp} showLabel={false} />
        </div>
      </div>
    </div>
  );
}

function SectorCell({ s }) {
  const bg = `color-mix(in oklch, ${tempColor(s.pct)} 22%, white)`;
  const border = `color-mix(in oklch, ${tempColor(s.pct)} 50%, var(--border))`;
  return (
    <div className="sector-cell" style={{ background: bg, boxShadow: `inset 0 0 0 1px ${border}` }}>
      <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between' }}>
        <div className="name">{s.name}</div>
        <span className={s.chg >= 0 ? 'tag up' : 'tag down'} style={{ fontSize: 10, padding: '1px 6px' }}>
          {s.chg >= 0 ? '+' : ''}{s.chg.toFixed(2)}%
        </span>
      </div>
      <div>
        <div className="pct">{s.pct}<span style={{ fontSize: 11, color: 'var(--ink-2)', marginLeft: 2 }}>分位</span></div>
        <div className="sub">PE {s.pe.toFixed(1)}</div>
      </div>
    </div>
  );
}

function Dashboard({ market, onPick }) {
  const series = window.MARKET_SERIES[market];
  const headlines = window.MARKET_HEADLINES[market];
  const sectors = window.SECTORS[market];
  const watchlist = window.INDEX_ROWS.filter(r => r.market === market && r.fav).slice(0, 6);

  // Aggregate market temperature = average of pep
  const tempAvg = headlines.reduce((a, b) => a + b.pep, 0) / headlines.length;

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
          <span className="pulse">数据流活跃 · 19:42</span>
          <span>更新至 2026/05/08</span>
        </div>
      </div>

      {/* Market thermometer summary */}
      <div className="card" style={{ marginBottom: 20, padding: '22px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, gap: 24, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--ink-3)', marginBottom: 4, letterSpacing: '.04em', textTransform: 'uppercase' }}>当前市场温度</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span className="mono" style={{ fontSize: 42, fontWeight: 500, letterSpacing: '-0.02em', color: tempColor(tempAvg) }}>{tempAvg.toFixed(1)}°</span>
              <span style={{ fontSize: 15, color: 'var(--ink-1)', fontWeight: 500 }}>{tempLabel(tempAvg)}</span>
              <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>较昨日 <span className="mono up">+1.2°</span></span>
            </div>
          </div>
          <div style={{ flex: 1, minWidth: 320, maxWidth: 520 }}>
            <div className="thermo-track" style={{ height: 10 }}>
              <div className="thermo-marker" style={{ left: `${tempAvg}%`, width: 18, height: 18, borderWidth: 3 }} />
            </div>
            <div className="thermo-ticks">
              <span>极度低估</span><span>低估</span><span>偏低</span><span>正常</span><span>偏高</span><span>高估</span><span>极度高估</span>
            </div>
          </div>
        </div>

        {/* Hero chart */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{market === 'cn' ? '全市场 PE 走势' : market === 'hk' ? '香港主要指数 PE 走势' : '美股主要指数 PE 走势'}</span>
              <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>近 20 年</span>
            </div>
            <div className="legend">
              {Object.keys(series).map((k, i) => (
                <span key={k} className="item"><span className="sw" style={{ background: PALETTE[i] }} /> {k}</span>
              ))}
            </div>
          </div>
          <div style={{ width: '100%', overflow: 'hidden' }}>
            <LC series={series} width={1340} height={300} palette={PALETTE} />
          </div>
        </div>
      </div>

      {/* Headline cards */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${headlines.length}, 1fr)`, gap: 12, marginBottom: 8 }}>
        {headlines.map((d, i) => <HeadlineCard key={d.name} d={d} palette={PALETTE[i]} />)}
      </div>

      {/* Sector heatmap */}
      <div className="section-head">
        <h2 className="section-title">行业温度图 <span className="count">{sectors.length} 个行业</span></h2>
        <div className="section-actions">
          <div className="toggle-group">
            <button className="on">分位</button>
            <button>涨跌</button>
            <button>PE</button>
          </div>
        </div>
      </div>
      <div className="sector-grid">
        {sectors.map(s => <SectorCell key={s.name} s={s} />)}
      </div>

      {/* Watchlist */}
      <div className="section-head">
        <h2 className="section-title">我的关注 <span className="count">{watchlist.length} 个指数</span></h2>
        <button className="btn" onClick={() => onPick('list')}>查看全部 →</button>
      </div>
      <div className="card" style={{ padding: 0 }}>
        {watchlist.map(r => (
          <div key={r.code} className="watch-row" onClick={() => onPick('detail', r)} style={{ cursor: 'pointer' }}>
            <div className="name">
              {r.name}
              <small>{r.code} · {r.sector}</small>
            </div>
            <div>
              <div className="mono" style={{ fontSize: 15, fontWeight: 500 }}>{r.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              <div className={'mono ' + (r.chg >= 0 ? 'up' : 'down')} style={{ fontSize: 11 }}>{r.chg >= 0 ? '+' : ''}{r.chg.toFixed(2)}%</div>
            </div>
            <SP data={window.seedSeries(r.sparkSeed, 60, 100, 1.4)} width={120} height={28} positive />
            <div>
              <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PE 分位</div>
              <PC p={r.pep} showLabel={false} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, color: 'var(--ink-3)', marginBottom: 2 }}>PB 分位</div>
              <PC p={r.pbp} showLabel={false} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

window.Dashboard = Dashboard;
