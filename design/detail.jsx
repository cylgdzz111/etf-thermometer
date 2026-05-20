// 指数详情 — detail view
const { LineChart: LC3, DistributionChart: DC3, PercentileChip: PC3, Sparkline: SP3 } = window.Charts;

function Detail({ row, onBack }) {
  const d = row ? {
    ...window.DETAIL_INDEX,
    name: row.name, code: row.code, market: row.market,
    close: row.close, chg: row.chg,
    pe: row.pe, pep: row.pep, pb: row.pb, pbp: row.pbp,
  } : window.DETAIL_INDEX;

  const [range, setRange] = React.useState('5y');
  const [tab, setTab] = React.useState('valuation');

  const len = range === '1y' ? 60 : range === '5y' ? 120 : 180;
  const priceSeries = { 收盘价: d.series.slice(-len), 'PE TTM': d.peSeries.slice(-len) };

  const overallTemp = Math.round((d.pep + d.pbp) / 2);

  return (
    <div>
      {/* Crumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 12, color: 'var(--ink-3)' }}>
        <button className="btn" style={{ padding: '4px 10px', fontSize: 12 }} onClick={onBack}>← 返回列表</button>
        <span>指数估值</span>
        <span>/</span>
        <span style={{ color: 'var(--ink-1)' }}>{d.name}</span>
      </div>

      {/* Header */}
      <div className="detail-head">
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <h1 className="page-title" style={{ margin: 0 }}>{d.name}</h1>
            <span className="tag">{d.code}</span>
            <span className="tag">{ {cn:'A 股', hk:'港股', us:'美股'}[d.market] }</span>
          </div>
          <div className="detail-meta">
            <span className="item"><b className="mono">{d.close.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</b></span>
            <span className={'item ' + (d.chg >= 0 ? 'up' : 'down')}>
              <b className={'mono ' + (d.chg >= 0 ? 'up' : 'down')}>{d.chg >= 0 ? '+' : ''}{d.chg.toFixed(2)}%</b>今日
            </span>
            <span className="item"><b className="mono up">+{d.totalRet.toFixed(2)}%</b>历史累计</span>
            <span className="item"><b className="mono down">{d.drawdown.toFixed(2)}%</b>距前高</span>
            <span className="item" style={{ color: 'var(--ink-3)' }}>更新至 2026/05/08</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn">♥ 收藏</button>
          <button className="btn">⇲ 设为基准</button>
          <button className="btn primary">网格策略 →</button>
        </div>
      </div>

      {/* Temperature banner */}
      <div className="card" style={{ padding: '16px 22px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, minWidth: 200 }}>
          <span style={{ fontSize: 11, color: 'var(--ink-3)', letterSpacing: '.04em', textTransform: 'uppercase' }}>综合温度</span>
          <span className="mono" style={{ fontSize: 36, fontWeight: 500, color: tempColor(overallTemp), letterSpacing: '-0.02em' }}>{overallTemp}°</span>
          <span style={{ fontSize: 14, color: 'var(--ink-1)', fontWeight: 500 }}>{tempLabel(overallTemp)}</span>
        </div>
        <div style={{ flex: 1 }}>
          <div className="thermo-track">
            <div className="thermo-marker" style={{ left: `${overallTemp}%` }} />
          </div>
          <div className="thermo-ticks">
            <span>0°</span><span>15°</span><span>30°</span><span>45°</span><span>60°</span><span>75°</span><span>90°</span><span>100°</span>
          </div>
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-2)', maxWidth: 260, lineHeight: 1.5 }}>
          PE 分位 <b className="mono" style={{ color: 'var(--ink) '}}>{d.pep.toFixed(1)}%</b>，
          PB 分位 <b className="mono" style={{ color: 'var(--ink) '}}>{d.pbp.toFixed(1)}%</b>。
          当前估值显著高于历史 80% 时间段。
        </div>
      </div>

      {/* Main chart + side panel */}
      <div className="detail-grid">
        <div className="card">
          <div className="card-head">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <h3 className="card-title">价格 & PE 走势</h3>
              <div className="toggle-group">
                {['1y', '5y', '10y'].map(r => (
                  <button key={r} className={range === r ? 'on' : ''} onClick={() => setRange(r)}>
                    {r === '1y' ? '近 1 年' : r === '5y' ? '近 5 年' : '上市以来'}
                  </button>
                ))}
              </div>
            </div>
            <div className="legend">
              <span className="item"><span className="sw" style={{ background: PALETTE[3] }} /> 收盘价</span>
              <span className="item"><span className="sw" style={{ background: PALETTE[0] }} /> PE TTM</span>
            </div>
          </div>
          <LC3 series={priceSeries} width={800} height={320} palette={[PALETTE[3], PALETTE[0]]} />
          {/* KPI strip */}
          <div className="kbar" style={{ marginTop: 16 }}>
            <div className="cell"><div className="l">最新 PE</div><div className="v" style={{ color: 'var(--accent)' }}>{d.pe.toFixed(2)}</div></div>
            <div className="cell"><div className="l">PE 平均值</div><div className="v">{d.peAvg.toFixed(2)}</div></div>
            <div className="cell"><div className="l">PE 最高</div><div className="v">{d.peMax.toFixed(2)}</div></div>
            <div className="cell"><div className="l">PE 最低</div><div className="v">{d.peMin.toFixed(2)}</div></div>
            <div className="cell"><div className="l">PE 分位</div><div className="v" style={{ color: tempColor(d.pep) }}>{d.pep.toFixed(1)}%</div></div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* PE distribution */}
          <div className="card">
            <div className="card-head">
              <h3 className="card-title">PE 估值分布</h3>
              <span className="card-hint">历史 PE 落入区间天数</span>
            </div>
            <div style={{ marginBottom: 10 }}>
              <DC3 data={d.peDist} current={Math.floor(d.peDist.length * 0.78)} width={460} height={110} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', marginTop: 4 }}>
                <span>{d.peMin.toFixed(0)}</span><span>{((d.peMin + d.peMax)/2).toFixed(0)}</span><span>{d.peMax.toFixed(0)}</span>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14 }}>
              {[{l:'当前分位', v: d.pep.toFixed(1)+'%', c: tempColor(d.pep), accent: true},
                {l:'20% 分位', v: '97.93'},
                {l:'50% 分位', v: '104.39'},
                {l:'80% 分位', v: '151.52'}].map((k, i) => (
                <div key={i} className="cell" style={{ background: k.accent ? `color-mix(in oklch, ${k.c} 14%, white)` : 'var(--surface-2)', borderRadius: 8, padding: '10px 12px' }}>
                  <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>{k.l}</div>
                  <div className="mono" style={{ fontSize: 16, fontWeight: 500, color: k.accent ? k.c : 'var(--ink)', marginTop: 2 }}>{k.v}</div>
                </div>
              ))}
            </div>
          </div>

          {/* PB distribution */}
          <div className="card">
            <div className="card-head">
              <h3 className="card-title">PB 估值分布</h3>
              <span className="card-hint">历史 PB 落入区间天数</span>
            </div>
            <DC3 data={d.pbDist} current={Math.floor(d.pbDist.length * 0.85)} width={460} height={90} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', marginTop: 4 }}>
              <span>{d.pbMin.toFixed(2)}</span><span>{((d.pbMin + d.pbMax)/2).toFixed(2)}</span><span>{d.pbMax.toFixed(2)}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, marginTop: 14 }}>
              {[{l:'当前 PB', v: d.pb.toFixed(2), c: tempColor(d.pbp), accent: true},
                {l:'最高', v: d.pbMax.toFixed(2)},
                {l:'最低', v: d.pbMin.toFixed(2)},
                {l:'均值', v: d.pbAvg.toFixed(2)}].map((k, i) => (
                <div key={i} style={{ background: k.accent ? `color-mix(in oklch, ${k.c} 14%, white)` : 'var(--surface-2)', borderRadius: 8, padding: '8px 10px' }}>
                  <div style={{ fontSize: 10.5, color: 'var(--ink-3)' }}>{k.l}</div>
                  <div className="mono" style={{ fontSize: 14, fontWeight: 500, color: k.accent ? k.c : 'var(--ink)', marginTop: 1 }}>{k.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Related indices */}
      <div className="section-head">
        <h2 className="section-title">同板块指数 <span className="count">推荐对比</span></h2>
      </div>
      <div className="card" style={{ padding: 0 }}>
        {window.INDEX_ROWS.filter(r => r.sector === (row?.sector || '军工')).slice(0, 4).map(r => (
          <div key={r.code} className="watch-row" style={{ cursor: 'pointer' }}>
            <div className="name">{r.name}<small>{r.code}</small></div>
            <div>
              <div className="mono" style={{ fontSize: 15 }}>{r.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
              <div className={'mono ' + (r.chg >= 0 ? 'up' : 'down')} style={{ fontSize: 11 }}>{r.chg >= 0 ? '+' : ''}{r.chg.toFixed(2)}%</div>
            </div>
            <SP3 data={window.seedSeries(r.sparkSeed, 60, 100, 1.4)} width={120} height={28} positive />
            <PC3 p={r.pep} showLabel={false} />
            <PC3 p={r.pbp} showLabel={false} />
          </div>
        ))}
      </div>
    </div>
  );
}

window.Detail = Detail;
