"""
计算所有指数的 PE/PB/PS/DYR 历史分位数（10年），更新 index_stats 表。
分位线（p30/p50/p80）改为在 history 接口按请求区间动态计算，此处不再存储。

用法：python -m scripts.calc_stats
"""
import asyncio
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, date, timedelta
import numpy as np
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.models.index import Index
from app.models.daily_metrics import DailyMetrics
from app.models.index_stats import IndexStats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

MIN_DAYS = 250


def _percentile_rank(series: np.ndarray, current: float) -> float:
    return float(np.sum(series <= current) / len(series) * 100)


def _calc_metric(values: np.ndarray, current: float | None):
    """返回 (percentile, min, max, avg) 或全 None。"""
    if len(values) < MIN_DAYS or current is None:
        return None, None, None, None
    return (
        round(_percentile_rank(values, current), 2),
        float(values.min()),
        float(values.max()),
        float(values.mean()),
    )


async def calc_all():
    async with AsyncSessionLocal() as session:
        indices = (await session.execute(
            select(Index).where(Index.is_active == True)  # noqa: E712
        )).scalars().all()
        logger.info('共 %d 个指数需要计算', len(indices))
        for idx in indices:
            await _calc_one(session, idx.code)
        await session.commit()
    logger.info('全部完成')


async def _calc_one(session, code: str):
    cutoff = date.today() - timedelta(days=365 * 10)
    rows = (await session.execute(
        select(DailyMetrics)
        .where(DailyMetrics.index_code == code, DailyMetrics.date >= cutoff)
        .order_by(DailyMetrics.date)
    )).scalars().all()

    if not rows:
        logger.info('%s: 无数据，跳过', code)
        return

    latest = rows[-1]

    pe_vals  = np.array([float(r.pe)  for r in rows if r.pe  is not None])
    pb_vals  = np.array([float(r.pb)  for r in rows if r.pb  is not None])
    ps_vals  = np.array([float(r.ps)  for r in rows if r.ps  is not None])
    dyr_vals = np.array([float(r.dyr) for r in rows if r.dyr is not None])

    pe_pct,  pe_min,  pe_max,  pe_avg  = _calc_metric(pe_vals,  float(latest.pe)  if latest.pe  is not None else None)
    pb_pct,  pb_min,  pb_max,  pb_avg  = _calc_metric(pb_vals,  float(latest.pb)  if latest.pb  is not None else None)
    ps_pct,  ps_min,  ps_max,  ps_avg  = _calc_metric(ps_vals,  float(latest.ps)  if latest.ps  is not None else None)
    dyr_pct, dyr_min, dyr_max, dyr_avg = _calc_metric(dyr_vals, float(latest.dyr) if latest.dyr is not None else None)

    existing = await session.get(IndexStats, code)
    fields = dict(
        pe_percentile=pe_pct,   pe_min=pe_min,   pe_max=pe_max,   pe_avg=pe_avg,
        pb_percentile=pb_pct,   pb_min=pb_min,   pb_max=pb_max,   pb_avg=pb_avg,
        ps_percentile=ps_pct,   ps_min=ps_min,   ps_max=ps_max,   ps_avg=ps_avg,
        dyr_percentile=dyr_pct, dyr_min=dyr_min, dyr_max=dyr_max, dyr_avg=dyr_avg,
        data_date=latest.date,
        updated_at=datetime.now(),
    )

    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        session.add(IndexStats(index_code=code, **fields))

    logger.info('%s: pe=%s pb=%s ps=%s dyr=%s rows=%d',
                code,
                f'{pe_pct:.1f}%'  if pe_pct  is not None else 'N/A',
                f'{pb_pct:.1f}%'  if pb_pct  is not None else 'N/A',
                f'{ps_pct:.1f}%'  if ps_pct  is not None else 'N/A',
                f'{dyr_pct:.1f}%' if dyr_pct is not None else 'N/A',
                len(rows))


async def main():
    await calc_all()
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
