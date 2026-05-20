// 指数估值列表 — list view
const { Sparkline: SP2, PercentileChip: PC2, PBar: PB2 } = window.Charts;

function IndexList({ market, onPick }) {
  const [search, setSearch] = React.useState('');
  const [valuationBucket, setValuationBucket] = React.useState('all'); // all/low/normal/high
  const [sectorFilter, setSectorFilter] = React.useState('all');
  const [sortKey, setSortKey] = React.useState('chg');
  const [sortDir, setSortDir] = React.useState('desc');
  const [favOnly, setFavOnly] = React.useState(false);

  const all = window.INDEX_ROWS.filter(r => r.market === market);
  const sectors = Array.from(new Set(all.map(r => r.sector)));

  const filtered = all.filter(r => {
    if (favOnly && !r.fav) return false;
    if (search && !(r.name.includes(search) || r.code.toLowerCase().includes(search.toLowerCase()))) return false;
    if (sectorFilter !== 'all' && r.sector !== sectorFilter) return false;
    if (valuationBucket === 'low' && r.pep > 30) return false;
    if (valuationBucket === 'normal' && (r.pep <= 30 || r.pep >= 70)) return false;
    if (valuationBucket === 'high' && r.pep < 70) return false;
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (av == null) return 1; if (bv == null) return -1;
    return sortDir === 'desc' ? bv - av : av - bv;
  });

  function toggleSort(k) {
    if (sortKey === k) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortKey(k); setSortDir('desc'); }
  }

  const buckets = [
    { id: 'all', label: '全部', count: all.length, swatch: null },
    { id: 'low', label: '低估', count: all.filter(r => r.pep <= 30).length, swatch: 'var(--temp-1)' },
    { id: 'normal', label: '正常', count: all.filter(r => r.pep > 30 && r.pep < 70).length, swatch: 'var(--temp-3)' },
    { id: 'high', label: '高估', count: all.filter(r => r.pep >= 70).length, swatch: 'var(--temp-5)' },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <h1 className="page-title">指数估值</h1>
          <p className="page-sub">
            300+ 全球指数估值数据，按温度分段、行业、分位灵活筛选。点击行查看详情。
            数据每日 19:00 ~ 21:00 更新。
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button className={'chip' + (favOnly ? ' active' : '')} onClick={() => setFavOnly(v => !v)}>
            <span>♥</span> 我的收藏
          </button>
          <div className="search" style={{ minWidth: 280 }}>
            <span style={{ color: 'var(--ink-3)' }}>⌕</span>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索指数代码或名称" />
          </div>
        </div>
      </div>

      <div className="filters">
        {buckets.map(b => (
          <button key={b.id} className={'chip' + (valuationBucket === b.id ? ' active' : '')} onClick={() => setValuationBucket(b.id)}>
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

      <div className="table-wrap">
        <table className="idx">
          <thead>
            <tr>
              <th>指数 / 代码</th>
              <th onClick={() => toggleSort('close')} style={{ cursor: 'pointer' }}>收盘价</th>
              <th onClick={() => toggleSort('chg')} style={{ cursor: 'pointer' }}>涨跌幅</th>
              <th>近 60 日</th>
              <th onClick={() => toggleSort('w52')} style={{ cursor: 'pointer' }}>52 周涨跌</th>
              <th onClick={() => toggleSort('peakDist')} style={{ cursor: 'pointer' }}>距历史最高</th>
              <th onClick={() => toggleSort('pe')} style={{ cursor: 'pointer' }}>PE</th>
              <th onClick={() => toggleSort('pep')} style={{ cursor: 'pointer' }}>PE 分位</th>
              <th onClick={() => toggleSort('pb')} style={{ cursor: 'pointer' }}>PB</th>
              <th onClick={() => toggleSort('pbp')} style={{ cursor: 'pointer' }}>PB 分位</th>
              <th style={{ textAlign: 'center' }}>温度</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(r => (
              <tr key={r.code} onClick={() => onPick('detail', r)}>
                <td>
                  <div className="name">{r.name}</div>
                  <div className="code">{r.code} · {r.sector}</div>
                </td>
                <td className="num">{r.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className={'num ' + (r.chg >= 0 ? 'up' : 'down')}>{r.chg >= 0 ? '+' : ''}{r.chg.toFixed(2)}%</td>
                <td><SP2 data={window.seedSeries(r.sparkSeed, 60, 100, 1.2)} width={80} height={22} positive /></td>
                <td className={'num ' + (r.w52 >= 0 ? 'up' : 'down')}>{r.w52 >= 0 ? '+' : ''}{r.w52.toFixed(2)}%</td>
                <td className={'num ' + (r.peakDist >= 0 ? 'flat' : 'down')}>{r.peakDist.toFixed(2)}%</td>
                <td className="num">{r.pe.toFixed(2)}</td>
                <td><PB2 p={r.pep} /></td>
                <td className="num">{r.pb.toFixed(2)}</td>
                <td><PB2 p={r.pbp} /></td>
                <td style={{ textAlign: 'center' }}>
                  <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: tempColor((r.pep + r.pbp) / 2), background: `color-mix(in oklch, ${tempColor((r.pep+r.pbp)/2)} 16%, white)`, padding: '3px 8px', borderRadius: 999 }}>
                    {Math.round((r.pep + r.pbp) / 2)}°
                  </span>
                </td>
                <td>
                  <span style={{ color: 'var(--accent)', fontSize: 12, fontWeight: 500 }}>分析 →</span>
                </td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr><td colSpan="12" style={{ textAlign: 'center', padding: '40px 12px', color: 'var(--ink-3)' }}>没有符合条件的指数</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 14, fontSize: 12, color: 'var(--ink-3)' }}>
        <span>显示 {sorted.length} / {all.length} 个指数</span>
        <span>排序：{ ({close:'收盘价',chg:'涨跌幅',w52:'52周涨跌',peakDist:'距历史最高',pe:'PE',pep:'PE分位',pb:'PB',pbp:'PB分位'})[sortKey] } · {sortDir === 'desc' ? '降序' : '升序'}</span>
      </div>
    </div>
  );
}

window.IndexList = IndexList;
