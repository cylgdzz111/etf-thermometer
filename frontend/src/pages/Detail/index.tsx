import { useParams, useNavigate } from 'react-router-dom';

export default function Detail() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 12, color: 'var(--ink-3)' }}>
        <button className="btn" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => navigate('/list')}>
          ← 返回列表
        </button>
        <span>指数估值 / {code}</span>
      </div>

      {/* TODO Phase 3: 接入真实数据 */}
      <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-3)' }}>
        指数详情数据接入中（Phase 3）— 代码：{code}
      </div>
    </div>
  );
}
