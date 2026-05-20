import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMarket } from '../../store/MarketContext';
import { useIndexList } from '../../api/index';
import Sparkline from '../../components/charts/Sparkline';
import PBar from '../../components/charts/PBar';
import { tempColor } from '../../utils/temperature';
import type { IndexRow } from '../../types';

type SortKey = 'close' | 'pe' | 'pep' | 'pb' | 'pbp' | 'temperature';

export default function IndexList() {
  const { market } = useMarket();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [valuationBucket, setValuationBucket] = useState<'all' | 'low' | 'normal' | 'high'>('all');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [sortKey, setSortKey] = useState<SortKey>('pep');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const { data: rows = [], isLoading, isError } = useIndexList({ market });

  const sectors = useMemo(() => Array.from(new Set(rows.map(r => r.sector).filter(Boolean))) as string[], [rows]);

  const filtered = useMemo(() => rows.filter(r => {
    if (search && !(r.name.includes(search) || r.code.toLowerCase().includes(search.toLowerCase()))) return false;
    if (sectorFilter !== 'all' && r.sector !== sectorFilter) return false;
    if (valuationBucket === 'low' && (r.pep == null || r.pep > 30)) return false;
    if (valuationBucket === 'normal' && (r.pep == null || r.pep <= 30 || r.pep >= 70)) return false;
    if (valuationBucket === 'high' && (r.pep == null || r.pep < 70)) return false;
    return true;
  }), [rows, search, sectorFilter, valuationBucket]);

  const sorted = useMemo(() => [...filtered].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    return sortDir === 'desc' ? bv - av : av - bv;
  }), [filtered, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (sortKey === k) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(k); setSortDir('asc'); }
  }

  function sortArrow(k: SortKey) {
    if (sortKey !== k) return null;
    return <span style={{ marginLeft: 3, opacity: 0.6 }}>{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  const buckets = [
    { id: 'all' as const, label: '全部', count: rows.length, swatch: null },
    { id: 'low' as const, label: '低估', count: rows.filter(r => r.pep != null && r.pep <= 30).length, swatch: 'var(--temp-1)' },
    { id: 'normal' as const, label: '正常', count: rows.filter(r => r.pep != null && r.pep > 30 && r.pep < 70).length, swatch: 'var(--temp-3)' },
    { id: 'high' as const, label: '高估', count: rows.filter(r => r.pep != null && r.pep >= 70).length, swatch: 'var(--temp-5)' },
  ];

  function TempBadge({ r }: { r: IndexRow }) {
    const t = r.temperature;
    if (t == null) return <span className="mono" style={{ color: 'var(--ink-3)' }}>—</span>;
    return (
      <span className="mono" style={{
        fontSize: 12, fontWeight: 600, color: tempColor(t),
        background: `color-mix(in oklch, ${tempColor(t)} 16%, white)`,
        padding: '3px 8px', borderRadius: 999,
      }}>
        {t.toFixed(0)}°
      </span>
    );
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1 className="page-title">指数估值</h1>
          <p className="page-sub">
            A 股全量指数估值数据，按温度分段、行业、分位灵活筛选。点击行查看详情。
            数据每日更新。
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="search" style={{ minWidth: 240 }}>
            <span style={{ color: 'var(--ink-3)' }}>⌕</span>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="搜索指数代码或名称"
            />
          </div>
        </div>
      </div>

      <div className="filters">
        {buckets.map(b => (
          <button
            key={b.id}
            className={'chip' + (valuationBucket === b.id ? ' active' : '')}
            onClick={() => setValuationBucket(b.id)}
          >
            {b.swatch && <span className="swatch" style={{ background: b.swatch }} />}
            {b.label}
            <span className="count">{b.count}</span>
          </button>
        ))}
        <span style={{ width: 1, height: 18, background: 'var(--border)', margin: '0 4px' }} />
        <button className={'chip' + (sectorFilter === 'all' ? ' active' : '')} onClick={() => setSectorFilter('all')}>全行业</button>
        {sectors.map(s => (
          <button key={s} className={'chip' + (sectorFilter === s ? ' active' : '')} onClick={() => setSectorFilter(s)}>{s}</button>
        ))}
      </div>

      {isLoading && (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>加载中…</div>
      )}
      {isError && (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>数据加载失败</div>
      )}

      {!isLoading && !isError && (
        <>
          <div className="table-wrap">
            <table className="idx">
              <thead>
                <tr>
                  <th>指数 / 代码</th>
                  <th className="num" onClick={() => toggleSort('close')} style={{ cursor: 'pointer' }}>收盘价{sortArrow('close')}</th>
                  <th>近 60 日</th>
                  <th className="num" onClick={() => toggleSort('pe')} style={{ cursor: 'pointer' }}>PE{sortArrow('pe')}</th>
                  <th onClick={() => toggleSort('pep')} style={{ cursor: 'pointer' }}>PE 分位{sortArrow('pep')}</th>
                  <th className="num" onClick={() => toggleSort('pb')} style={{ cursor: 'pointer' }}>PB{sortArrow('pb')}</th>
                  <th onClick={() => toggleSort('pbp')} style={{ cursor: 'pointer' }}>PB 分位{sortArrow('pbp')}</th>
                  <th style={{ textAlign: 'center' }} onClick={() => toggleSort('temperature')} >温度{sortArrow('temperature')}</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(r => (
                  <tr key={r.code} onClick={() => navigate(`/detail/${r.code}`)}>
                    <td>
                      <div className="name">{r.name}</div>
                      <div className="code">{r.code}{r.sector ? ` · ${r.sector}` : ''}</div>
                    </td>
                    <td className="num">{r.close != null ? r.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}</td>
                    <td>{r.sparkline.length > 1 ? <Sparkline data={r.sparkline} width={80} height={22} /> : <span style={{ color: 'var(--ink-4)' }}>—</span>}</td>
                    <td className="num">{r.pe != null ? r.pe.toFixed(2) : '—'}</td>
                    <td><PBar p={r.pep} /></td>
                    <td className="num">{r.pb != null ? r.pb.toFixed(4) : '—'}</td>
                    <td><PBar p={r.pbp} /></td>
                    <td style={{ textAlign: 'center' }}><TempBadge r={r} /></td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '40px 12px', color: 'var(--ink-3)' }}>
                      没有符合条件的指数
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 14, fontSize: 12, color: 'var(--ink-3)' }}>
            <span>显示 {sorted.length} / {rows.length} 个指数</span>
            <span>排序：{({ close: '收盘价', pe: 'PE', pep: 'PE分位', pb: 'PB', pbp: 'PB分位', temperature: '温度' })[sortKey]} · {sortDir === 'asc' ? '升序' : '降序'}</span>
          </div>
        </>
      )}
    </div>
  );
}
