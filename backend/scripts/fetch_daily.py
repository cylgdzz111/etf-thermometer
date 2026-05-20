"""
每日数据抓取 + 分位数计算

两种运行模式：
  1. 定时服务：python -m scripts.fetch_daily          → APScheduler，每日 20:00 执行
  2. 手动触发：python -m scripts.fetch_daily --now    → 立即执行一次后退出
  3. 历史回填：python -m scripts.fetch_daily --backfill → 抓取全量历史后退出
"""
import argparse
import asyncio
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta

from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal, engine
from app.models.index import Index
from app.models.daily_metrics import DailyMetrics as DailyMetricsModel
from providers.composite import CompositeProvider
from scripts.calc_stats import calc_all

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger('fetch_daily')

provider = CompositeProvider()

# 历史回填起始年数
BACKFILL_YEARS = 11


async def fetch_index(code: str, market: str, start_date: date):
    """抓取单个指数从 start_date 至今的数据，跳过已有记录"""
    try:
        records = provider.get_history(code, market, start_date)
    except Exception as e:
        logger.error('抓取失败 %s: %s', code, e)
        return 0

    if not records:
        return 0

    async with AsyncSessionLocal() as session:
        inserted = 0
        for r in records:
            # 已存在则跳过（uq_code_date 约束保证唯一性）
            exists = (await session.execute(
                select(DailyMetricsModel.id)
                .where(DailyMetricsModel.index_code == r.index_code,
                       DailyMetricsModel.date == r.date)
                .limit(1)
            )).scalar_one_or_none()
            if exists:
                continue
            session.add(DailyMetricsModel(
                index_code=r.index_code,
                date=r.date,
                close=r.close,
                pe=r.pe,
                pb=r.pb,
                source=r.source,
            ))
            inserted += 1
        await session.commit()
    return inserted


async def get_latest_date(code: str) -> date | None:
    """查询该指数在 daily_metrics 中最新的数据日期"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.max(DailyMetricsModel.date))
            .where(DailyMetricsModel.index_code == code)
        )
        return result.scalar_one_or_none()


async def run_daily():
    """增量更新：从每个指数的最新日期起抓取"""
    logger.info('=== 开始每日增量更新 ===')
    async with AsyncSessionLocal() as session:
        indices = (await session.execute(select(Index))).scalars().all()

    total_inserted = 0
    for idx in indices:
        latest = await get_latest_date(idx.code)
        # 如果有历史数据，从最新日期的次日开始；否则只取近 30 天（等待 backfill）
        if latest:
            start = latest + timedelta(days=1)
        else:
            start = date.today() - timedelta(days=30)

        if start > date.today():
            logger.info('%s: 已是最新，跳过', idx.code)
            continue

        n = await fetch_index(idx.code, idx.market, start)
        logger.info('%s: 新增 %d 条', idx.code, n)
        total_inserted += n

    logger.info('=== 增量更新完成，共新增 %d 条 ===', total_inserted)

    # 更新分位数缓存
    logger.info('=== 开始计算分位数 ===')
    await calc_all()


async def run_backfill():
    """历史回填：抓取全量历史数据"""
    logger.info('=== 开始历史回填（近 %d 年）===', BACKFILL_YEARS)
    start_date = date(date.today().year - BACKFILL_YEARS, 1, 1)

    async with AsyncSessionLocal() as session:
        indices = (await session.execute(select(Index))).scalars().all()

    for idx in indices:
        logger.info('回填 %s %s', idx.code, idx.name)
        n = await fetch_index(idx.code, idx.market, start_date)
        logger.info('%s: 新增 %d 条', idx.code, n)

    logger.info('=== 历史回填完成 ===')
    logger.info('=== 开始计算分位数 ===')
    await calc_all()


async def main_async(mode: str):
    try:
        if mode == 'backfill':
            await run_backfill()
        else:
            await run_daily()
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--now', action='store_true', help='立即执行一次后退出')
    parser.add_argument('--backfill', action='store_true', help='历史回填后退出')
    args = parser.parse_args()

    if args.backfill:
        asyncio.run(main_async('backfill'))
        return

    if args.now:
        asyncio.run(main_async('daily'))
        return

    # 定时服务模式
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(
        lambda: asyncio.run(main_async('daily')),
        CronTrigger(hour=20, minute=0),
        id='daily_fetch',
        max_instances=1,
        coalesce=True,
    )
    logger.info('定时任务已启动，每日 20:00 (Asia/Shanghai) 执行')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('调度器已停止')


if __name__ == '__main__':
    main()
