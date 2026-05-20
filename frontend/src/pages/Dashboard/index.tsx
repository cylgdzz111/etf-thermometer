import { useMarket } from '../../store/MarketContext';

export default function Dashboard() {
  const { market } = useMarket();

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
          <span>当前市场：{market.toUpperCase()}</span>
        </div>
      </div>

      {/* TODO Phase 3: 接入真实数据 */}
      <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>
        数据接入中（Phase 3）
      </div>
    </div>
  );
}
