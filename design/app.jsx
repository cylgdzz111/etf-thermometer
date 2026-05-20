// App shell — nav + view router
const { useState: useS, useEffect: useE } = React;

function MarketSwitch({ value, onChange }) {
  return (
    <div className="market-switch">
      {window.MARKETS.map(m => (
        <button key={m.id} className={value === m.id ? 'on' : ''} onClick={() => onChange(m.id)}>
          {m.label}
          <span style={{ opacity: .55, fontSize: 10.5, fontFamily: 'var(--font-mono)', marginLeft: 2 }}>{m.sub}</span>
        </button>
      ))}
    </div>
  );
}

function Nav({ view, onView, market, onMarket }) {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <div className="brand">
          <span className="brand-mark" />
          <span className="brand-name">ETF 温度计 <em>Thermometer</em></span>
        </div>

        <div className="nav-tabs">
          <button className={'nav-tab' + (view === 'dashboard' ? ' active' : '')} onClick={() => onView('dashboard')}>市场估值概览</button>
          <button className={'nav-tab' + (view === 'list' || view === 'detail' ? ' active' : '')} onClick={() => onView('list')}>指数估值</button>
          <button className="nav-tab">网格策略</button>
          <button className="nav-tab">相关性</button>
          <button className="nav-tab">资讯</button>
        </div>

        <MarketSwitch value={market} onChange={onMarket} />

        <div className="nav-right">
          <div className="search">
            <span style={{ color: 'var(--ink-3)' }}>⌕</span>
            <input placeholder="搜索指数 / ETF…" />
            <kbd>⌘K</kbd>
          </div>
          <button className="icon-btn" title="主题">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></svg>
          </button>
          <button className="icon-btn" title="账号">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 21v-1a8 8 0 0 1 16 0v1" /></svg>
          </button>
        </div>
      </div>
    </nav>
  );
}

function App() {
  const [view, setView] = useS('dashboard');
  const [market, setMarket] = useS('cn');
  const [activeRow, setActiveRow] = useS(null);

  // Persist
  useE(() => {
    const saved = JSON.parse(localStorage.getItem('etf-state') || '{}');
    if (saved.view) setView(saved.view);
    if (saved.market) setMarket(saved.market);
    if (saved.activeRow) setActiveRow(saved.activeRow);
  }, []);
  useE(() => {
    localStorage.setItem('etf-state', JSON.stringify({ view, market, activeRow }));
  }, [view, market, activeRow]);

  function handlePick(target, row) {
    if (target === 'detail') {
      setActiveRow(row);
      setView('detail');
      window.scrollTo({ top: 0, behavior: 'instant' });
    } else if (target === 'list') {
      setView('list');
    }
  }

  return (
    <div className="app">
      <Nav view={view} onView={setView} market={market} onMarket={setMarket} />
      <main className="page">
        {view === 'dashboard' && <window.Dashboard market={market} onPick={handlePick} />}
        {view === 'list' && <window.IndexList market={market} onPick={handlePick} />}
        {view === 'detail' && <window.Detail row={activeRow} onBack={() => setView('list')} />}
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
