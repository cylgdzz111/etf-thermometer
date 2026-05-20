import { NavLink } from 'react-router-dom';
import MarketSwitch from './MarketSwitch';
import { useMarket } from '../../store/MarketContext';

export default function Nav() {
  const { market, setMarket } = useMarket();

  return (
    <nav className="nav">
      <div className="nav-inner">
        <div className="brand">
          <span className="brand-mark" />
          <span className="brand-name">ETF 温度计 <em>Thermometer</em></span>
        </div>

        <div className="nav-tabs">
          <NavLink to="/" end className={({ isActive }) => 'nav-tab' + (isActive ? ' active' : '')}>
            市场估值概览
          </NavLink>
          <NavLink to="/list" className={({ isActive }) => 'nav-tab' + (isActive ? ' active' : '')}>
            指数估值
          </NavLink>
          <span className="nav-tab disabled">网格策略</span>
          <span className="nav-tab disabled">相关性</span>
        </div>

        <MarketSwitch value={market} onChange={setMarket} />

        <div className="nav-right">
          <div className="search">
            <span style={{ color: 'var(--ink-3)' }}>⌕</span>
            <input placeholder="搜索指数 / ETF…" readOnly />
            <kbd>⌘K</kbd>
          </div>
        </div>
      </div>
    </nav>
  );
}
