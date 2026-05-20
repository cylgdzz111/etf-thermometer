import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useIndexDetail, useIndexHistory } from '../../api/index';
import LineChart from '../../components/charts/LineChart';
import type { ReferenceLine } from '../../components/charts/LineChart';
import DistributionChart from '../../components/charts/DistributionChart';
import PercentileChip from '../../components/charts/PercentileChip';
import { tempColor, tempLabel } from '../../utils/temperature';
import type { IndexDetail, IndexHistory, RangeStats } from '../../types';

type Metric = 'pe' | 'pb' | 'ps' | 'dyr';
type Range  = '1y' | '3y' | '5y' | '10y' | 'all';

const MARKET_LABEL: Record<string, string> = { cn: 'A 股', hk: '港股', us: '美股' };

const RANGE_OPTIONS: { id: Range; label: string }[] = [
  { id: '1y',  label: '近 1 年' },
  { id: '3y',  label: '近 3 年' },
  { id: '5y',  label: '近 5 年' },
  { id: '10y', label: '近 10 年' },
  { id: 'all', label: '上市以来' },
];

const METRIC_OPTIONS: { id: Metric; label: string }[] = [
  { id: 'pe',  label: 'PE' },
  { id: 'pb',  label: 'PB' },
  { id: 'ps',  label: 'PS' },
  { id: 'dyr', label: '股息率' },
];

interface MetricConfig {
  series:     (h: IndexHistory) => (number | null)[];
  rangeStats: (h: IndexHistory) => RangeStats;
  current:    (d: IndexDetail)  => number | null;
  pct10y:     (d: IndexDetail)  => number | null;
  min:        (d: IndexDetail)  => number | null;
  max:        (d: IndexDetail)  => number | null;
  avg:        (d: IndexDetail)  => number | null;
  dist:       (d: IndexDetail)  => number[];
  distMin:    (d: IndexDetail)  => number | null;
  distMax:    (d: IndexDetail)  => number | null;
  fmt: (v: number) => string;
  bucketIdx:  (d: IndexDetail)  => number | undefined;
  // 图表 y 轴缩放倍数（原始值 × yScale 后传给 LineChart）
  yScale?: number;
}

function _bucketIdx(val: number | null, mn: number | null, mx: number | null, bins: number): number | undefined {
  if (val == null || mn == null || mx == null || bins === 0) return undefined;
  return Math.min(Math.floor((val - mn) / ((mx - mn) / bins)), bins - 1);
}

const METRIC_CONFIG: Record<Metric, MetricConfig> = {
  pe: {
    series:     h => h.pe,
    rangeStats: h => h.pe_stats,
    current:    d => d.pe,
    pct10y:     d => d.pep,
    min: d => d.pe_min, max: d => d.pe_max, avg: d => d.pe_avg,
    dist: d => d.pe_dist, distMin: d => d.pe_dist_min, distMax: d => d.pe_dist_max,
    fmt: v => v.toFixed(2),
    bucketIdx: d => _bucketIdx(d.pe, d.pe_dist_min, d.pe_dist_max, d.pe_dist.length),
  },
  pb: {
    series:     h => h.pb,
    rangeStats: h => h.pb_stats,
    current:    d => d.pb,
    pct10y:     d => d.pbp,
    min: d => d.pb_min, max: d => d.pb_max, avg: d => d.pb_avg,
    dist: d => d.pb_dist, distMin: d => d.pb_dist_min, distMax: d => d.pb_dist_max,
    fmt: v => v.toFixed(4),
    bucketIdx: d => _bucketIdx(d.pb, d.pb_dist_min, d.pb_dist_max, d.pb_dist.length),
  },
  ps: {
    series:     h => h.ps,
    rangeStats: h => h.ps_stats,
    current:    d => d.ps,
    pct10y:     d => d.psp,
    min: d => d.ps_min, max: d => d.ps_max, avg: d => d.ps_avg,
    dist: d => d.ps_dist, distMin: d => d.ps_dist_min, distMax: d => d.ps_dist_max,
    fmt: v => v.toFixed(4),
    bucketIdx: d => _bucketIdx(d.ps, d.ps_dist_min, d.ps_dist_max, d.ps_dist.length),
  },
  dyr: {
    series:     h => h.dyr,
    rangeStats: h => h.dyr_stats,
    current:    d => d.dyr,
    pct10y:     d => d.dyrp,
    min: d => d.dyr_min, max: d => d.dyr_max, avg: d => d.dyr_avg,
    dist: d => d.dyr_dist, distMin: d => d.dyr_dist_min, distMax: d => d.dyr_dist_max,
    fmt: v => (v * 100).toFixed(2) + '%',
    bucketIdx: d => _bucketIdx(d.dyr, d.dyr_dist_min, d.dyr_dist_max, d.dyr_dist.length),
    yScale: 100,
  },
};

function buildRefLines(stats: RangeStats): ReferenceLine[] {
  const lines: ReferenceLine[] = [];
  if (stats.p30 != null) lines.push({ value: stats.p30, label: '30%', color: 'var(--temp-1)', dashArray: '4 3' });
  if (stats.p50 != null) lines.push({ value: stats.p50, label: '50%', color: 'var(--temp-3)', dashArray: '4 3' });
  if (stats.p80 != null) lines.push({ value: stats.p80, label: '80%', color: 'var(--temp-5)', dashArray: '4 3' });
  return lines;
}

export default function Detail() {
  const { code = '' } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [metric, setMetric] = useState<Metric>('pe');
  const [range, setRange] = useState<Range>('5y');

  const { data: detail, isLoading: loadingDetail, isError: errorDetail } = useIndexDetail(code);
  const { data: history, isLoading: loadingHistory } = useIndexHistory(code, range);

  if (loadingDetail) {
    return (
      <div>
        <button className="btn" style={{ padding: '4px 10px', fontSize: 12, marginBottom: 16 }} onClick={() => navigate('/list')}>← 返回列表</button>
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>加载中…</div>
      </div>
    );
  }
  if (errorDetail || !detail) {
    return (
      <div>
        <button className="btn" style={{ padding: '4px 10px', fontSize: 12, marginBottom: 16 }} onClick={() => navigate('/list')}>← 返回列表</button>
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>数据加载失败</div>
      </div>
    );
  }

  const cfg = METRIC_CONFIG[metric];
  const overallTemp = detail.temperature;

  // 分位线 & 区间分位：来自 history（随区间切换实时变化）
  const rangeStats: RangeStats = history ? cfg.rangeStats(history) : { p30: null, p50: null, p80: null, pct: null };

  const metricLabel = METRIC_OPTIONS.find(m => m.id === metric)!.label;
  const yScale = cfg.yScale ?? 1;
  const scaledSeries = (s: (number | null)[]) => yScale === 1 ? s : s.map(v => v == null ? null : v * yScale);
  const scaledStats  = (st: RangeStats): RangeStats => yScale === 1 ? st : {
    p30: st.p30 == null ? null : st.p30 * yScale,
    p50: st.p50 == null ? null : st.p50 * yScale,
    p80: st.p80 == null ? null : st.p80 * yScale,
    pct: st.pct,
  };
  const refLines = buildRefLines(scaledStats(rangeStats));
  const metricSeries = history ? { [metricLabel]: scaledSeries(cfg.series(history)) } : null;
  const priceSeries  = history?.price.some(v => v != null) ? { '收盘价': history!.price } : null;

  const cur  = cfg.current(detail);
  const dist = cfg.dist(detail);
  const distMin = cfg.distMin(detail);
  const distMax = cfg.distMax(detail);

  // 区间内分位（图表区间动态）vs 10年分位（全局温度用）
  const rangePct = rangeStats.pct;
  const pct10y   = cfg.pct10y(detail);

  return (
    <div>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 12, color: 'var(--ink-3)' }}>
        <button className="btn" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => navigate('/list')}>← 返回列表</button>
        <span>指数估值 /</span>
        <span style={{ color: 'var(--ink-1)' }}>{detail.name}</span>
      </div>

      {/* Header */}
      <div className="detail-head">
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
            <h1 className="page-title" style={{ margin: 0 }}>{detail.name}</h1>
            <span className="tag">{detail.code}</span>
            <span className="tag">{MARKET_LABEL[detail.market] ?? detail.market}</span>
            {detail.sector && <span className="tag">{detail.sector}</span>}
          </div>
          <div className="detail-meta" style={{ marginTop: 8 }}>
            {detail.close != null && (
              <span className="item">
                <b className="mono">{detail.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</b>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Temperature banner */}
      <div className="card" style={{ padding: '16px 22px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, minWidth: 200 }}>
          <span style={{ fontSize: 11, color: 'var(--ink-3)', letterSpacing: '.04em', textTransform: 'uppercase' }}>综合温度</span>
          <span className="mono" style={{ fontSize: 36, fontWeight: 500, color: tempColor(overallTemp), letterSpacing: '-0.02em' }}>
            {overallTemp != null ? `${overallTemp.toFixed(0)}°` : '—'}
          </span>
          {overallTemp != null && (
            <span style={{ fontSize: 14, color: 'var(--ink-1)', fontWeight: 500 }}>{tempLabel(overallTemp)}</span>
          )}
        </div>
        <div style={{ flex: 1 }}>
          {overallTemp != null && (
            <>
              <div className="thermo-track">
                <div className="thermo-marker" style={{ left: `${overallTemp}%` }} />
              </div>
              <div className="thermo-ticks">
                <span>0°</span><span>15°</span><span>30°</span><span>45°</span><span>60°</span><span>75°</span><span>90°</span><span>100°</span>
              </div>
            </>
          )}
        </div>
        {/* 10年分位汇总 */}
        <div style={{ fontSize: 12, color: 'var(--ink-2)', maxWidth: 260, lineHeight: 1.6 }}>
          <div style={{ fontSize: 10, color: 'var(--ink-3)', marginBottom: 2 }}>10年分位</div>
          PE {detail.pep != null ? `${detail.pep.toFixed(1)}%` : '—'}
          {' · '}PB {detail.pbp != null ? `${detail.pbp.toFixed(1)}%` : '—'}
          {detail.psp  != null && ` · PS ${detail.psp.toFixed(1)}%`}
          {detail.dyrp != null && ` · 股息率 ${detail.dyrp.toFixed(1)}%`}
        </div>
      </div>

      {/* Metric + Range controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <div className="toggle-group">
          {METRIC_OPTIONS.map(m => (
            <button key={m.id} className={metric === m.id ? 'on' : ''} onClick={() => setMetric(m.id)}>{m.label}</button>
          ))}
        </div>
        <div className="toggle-group">
          {RANGE_OPTIONS.map(r => (
            <button key={r.id} className={range === r.id ? 'on' : ''} onClick={() => setRange(r.id)}>{r.label}</button>
          ))}
        </div>
      </div>

      {/* Main grid */}
      <div className="detail-grid">
        {/* Left: charts + KPI */}
        <div className="card">
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--ink-3)' }}>{metricLabel} 走势</span>
              {refLines.length > 0 && (
                <span style={{ fontSize: 10, color: 'var(--ink-3)', display: 'flex', gap: 10 }}>
                  {refLines.map(rl => (
                    <span key={rl.label} style={{ color: rl.color }}>— {rl.label} 分位线</span>
                  ))}
                </span>
              )}
            </div>

            {loadingHistory ? (
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-3)' }}>加载中…</div>
            ) : metricSeries ? (
              <LineChart
                series={metricSeries}
                dates={history?.dates}
                referenceLines={refLines}
                width={780}
                height={220}
                palette={['#c66a1c']}
              />
            ) : (
              <div style={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-3)', fontSize: 12 }}>暂无数据</div>
            )}
          </div>

          {priceSeries && !loadingHistory && (
            <div style={{ paddingTop: 8, borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, color: 'var(--ink-3)', marginBottom: 6 }}>收盘价</div>
              <LineChart series={priceSeries} dates={history?.dates} width={780} height={140} palette={['#5fa180']} />
            </div>
          )}

          {/* KPI strip：区间内统计 */}
          <div className="kbar" style={{ marginTop: 16 }}>
            <div className="cell">
              <div className="l">当前值</div>
              <div className="v" style={{ color: 'var(--accent)' }}>{cur != null ? cfg.fmt(cur) : '—'}</div>
            </div>
            <div className="cell">
              <div className="l">均值</div>
              <div className="v">{cfg.avg(detail) != null ? cfg.fmt(cfg.avg(detail)!) : '—'}</div>
            </div>
            <div className="cell">
              <div className="l">区间分位</div>
              <div className="v" style={{ color: tempColor(rangePct) }}>
                {rangePct != null ? `${rangePct.toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="cell">
              <div className="l">10年分位</div>
              <div className="v" style={{ color: tempColor(pct10y) }}>
                {pct10y != null ? `${pct10y.toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="cell">
              <div className="l">30% / 50% / 80%</div>
              <div className="v" style={{ fontSize: 11, letterSpacing: '0.02em' }}>
                {rangeStats.p30 != null ? cfg.fmt(rangeStats.p30) : '—'}
                {' / '}
                {rangeStats.p50 != null ? cfg.fmt(rangeStats.p50) : '—'}
                {' / '}
                {rangeStats.p80 != null ? cfg.fmt(rangeStats.p80) : '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Right: distribution + quick stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="card-head">
              <h3 className="card-title">{metricLabel} 全历史分布</h3>
              <span className="card-hint">落入区间天数</span>
            </div>

            {dist.length > 0 ? (
              <>
                <DistributionChart data={dist} current={cfg.bucketIdx(detail)} width={440} height={110} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-3)', marginTop: 4 }}>
                  <span>{distMin != null ? cfg.fmt(distMin) : '—'}</span>
                  <span>{distMin != null && distMax != null ? cfg.fmt((distMin + distMax) / 2) : '—'}</span>
                  <span>{distMax != null ? cfg.fmt(distMax) : '—'}</span>
                </div>

                {/* 分位线值 */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14 }}>
                  {[
                    { l: `区间分位（${RANGE_OPTIONS.find(r => r.id === range)!.label}）`, v: rangePct != null ? `${rangePct.toFixed(1)}%` : '—', c: tempColor(rangePct), accent: true },
                    { l: '30% 分位线', v: rangeStats.p30 != null ? cfg.fmt(rangeStats.p30) : '—', c: 'var(--temp-1)' },
                    { l: '50% 分位线', v: rangeStats.p50 != null ? cfg.fmt(rangeStats.p50) : '—', c: 'var(--temp-3)' },
                    { l: '80% 分位线', v: rangeStats.p80 != null ? cfg.fmt(rangeStats.p80) : '—', c: 'var(--temp-5)' },
                  ].map((k, i) => (
                    <div key={i} style={{
                      background: k.accent ? `color-mix(in oklch, ${k.c} 14%, white)` : 'var(--surface-2)',
                      borderRadius: 8, padding: '10px 12px',
                    }}>
                      <div style={{ fontSize: 11, color: 'var(--ink-3)' }}>{k.l}</div>
                      <div className="mono" style={{ fontSize: 15, fontWeight: 500, color: k.c ?? 'var(--ink)', marginTop: 2 }}>{k.v}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--ink-3)', fontSize: 12, padding: '20px 0' }}>暂无分布数据</div>
            )}

            <div style={{ marginTop: 12 }}>
              <PercentileChip p={pct10y} />
              <span style={{ fontSize: 10, color: 'var(--ink-3)', marginLeft: 6 }}>10年</span>
            </div>
          </div>

          {/* 四指标快览 */}
          <div className="card">
            <div className="card-head"><h3 className="card-title">估值快览</h3></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {([
                { id: 'pe'  as Metric, label: 'PE',   val: detail.pe,  pct: detail.pep,  fmt: (v: number) => v.toFixed(2) },
                { id: 'pb'  as Metric, label: 'PB',   val: detail.pb,  pct: detail.pbp,  fmt: (v: number) => v.toFixed(4) },
                { id: 'ps'  as Metric, label: 'PS',   val: detail.ps,  pct: detail.psp,  fmt: (v: number) => v.toFixed(4) },
                { id: 'dyr' as Metric, label: '股息率', val: detail.dyr, pct: detail.dyrp, fmt: (v: number) => (v * 100).toFixed(2) + '%' },
              ]).map(item => (
                <div key={item.id}
                  onClick={() => setMetric(item.id)}
                  style={{
                    background: 'var(--surface-2)',
                    borderRadius: 8, padding: '10px 12px', cursor: 'pointer',
                    outline: metric === item.id ? '2px solid var(--accent)' : 'none',
                  }}>
                  <div style={{ fontSize: 11, color: 'var(--ink-3)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>{item.label}</span>
                    {item.pct != null && <span style={{ color: tempColor(item.pct) }}>{item.pct.toFixed(0)}% <span style={{ opacity: 0.5 }}>10y</span></span>}
                  </div>
                  <div className="mono" style={{ fontSize: 15, fontWeight: 500, marginTop: 3 }}>
                    {item.val != null ? item.fmt(item.val) : '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
