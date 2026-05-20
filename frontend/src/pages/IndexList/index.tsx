import { useMarket } from '../../store/MarketContext';

export default function IndexList() {
  const { market } = useMarket();

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
      </div>

      {/* TODO Phase 3: 接入真实数据，当前市场: {market} */}
      <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>
        数据接入中（Phase 3）— 市场：{market.toUpperCase()}
      </div>
    </div>
  );
}
