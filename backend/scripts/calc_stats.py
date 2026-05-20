"""
计算所有指数的 PE/PB 历史分位数，更新 index_stats 表
用法：python -m scripts.calc_stats
"""
import asyncio
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, date, timedelta
import numpy as np
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, engine
from app.models.index import Index
from app.models.daily_metrics import DailyMetrics
from app.models.index_stats import IndexStats

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# 分位数计算所需最少数据天数（少于此视为数据不足，不写入分位数）
MIN_PE_DAYS = 250


def _percentile_rank(series: np.ndarray, current: float) -> float:
    """当前值在历史序列中的百分位排名（0-100）"""
    return float(np.sum(series <= current) / len(series) * 100)


async def calc_all():
    async with AsyncSessionLocal() as session:
        # 获取所有指数
        indices = (await session.execute(select(Index))).scalars().all()
        logger.info('共 %d 个指数需要计算', len(indices))

        for idx in indices:
            await _calc_one(session, idx.code)

        await session.commit()
        logger.info('全部完成')


async def _calc_one(session, code: str):
    cutoff = date.today() - timedelta(days=365 * 10)   # 取近 10 年
    rows = (await session.execute(
        select(DailyMetrics)
        .where(DailyMetrics.index_code == code, DailyMetrics.date >= cutoff)
        .order_by(DailyMetrics.date)
    )).scalars().all()

    if not rows:
        logger.info('%s: 无数据，跳过', code)
        return

    # 最新一条
    latest = rows[-1]

    # PE 分位数
    pe_values = np.array([float(r.pe) for r in rows if r.pe is not None])
    pe_pct = pe_min = pe_max = pe_avg = None
    if len(pe_values) >= MIN_PE_DAYS and latest.pe is not None:
        pe_pct = _percentile_rank(pe_values, float(latest.pe))
        pe_min = float(pe_values.min())
        pe_max = float(pe_values.max())
        pe_avg = float(pe_values.mean())

    # PB 分位数
    pb_values = np.array([float(r.pb) for r in rows if r.pb is not None])
    pb_pct = pb_min = pb_max = pb_avg = None
    if len(pb_values) >= MIN_PE_DAYS and latest.pb is not None:
        pb_pct = _percentile_rank(pb_values, float(latest.pb))
        pb_min = float(pb_values.min())
        pb_max = float(pb_values.max())
        pb_avg = float(pb_values.mean())

    # 综合温度 = (PE分位 + PB分位) / 2，任一为空则为 None
    temperature = (pe_pct + pb_pct) / 2 if (pe_pct is not None and pb_pct is not None) else None

    # upsert index_stats
    existing = await session.get(IndexStats, code)
    if existing:
        existing.pe_percentile = pe_pct
        existing.pb_percentile = pb_pct
        existing.pe_min = pe_min
        existing.pe_max = pe_max
        existing.pe_avg = pe_avg
        existing.pb_min = pb_min
        existing.pb_max = pb_max
        existing.pb_avg = pb_avg
        existing.temperature = temperature
        existing.updated_at = datetime.now()
    else:
        session.add(IndexStats(
            index_code=code,
            pe_percentile=pe_pct,
            pb_percentile=pb_pct,
            pe_min=pe_min, pe_max=pe_max, pe_avg=pe_avg,
            pb_min=pb_min, pb_max=pb_max, pb_avg=pb_avg,
            temperature=temperature,
            updated_at=datetime.now(),
        ))

    logger.info('%s: pe_pct=%.1f%% pb_pct=%s rows=%d',
                code,
                pe_pct if pe_pct is not None else -1,
                f'{pb_pct:.1f}%' if pb_pct is not None else 'N/A',
                len(rows))


async def main():
    await calc_all()
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
