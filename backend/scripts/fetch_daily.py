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
from app.core.config import settings
from app.models.index import Index
from app.models.daily_metrics import DailyMetrics as DailyMetricsModel
from providers.composite import CompositeProvider
from providers.lixinger_provider import LixingerProvider
from providers.base import DataFetchError
from scripts.calc_stats import calc_all

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger('fetch_daily')

provider = CompositeProvider()

# 历史回填起始年数
BACKFILL_YEARS = 11


async def fetch_index(code: str, market: str, start_date: date, update_pe: bool = False):
    """抓取单个指数从 start_date 至今的数据。
    update_pe=True 时只补充已有记录中 pe/pb 为 NULL 的字段，不插入新行。
    """
    try:
        records = provider.get_history(code, market, start_date)
    except Exception as e:
        logger.error('抓取失败 %s: %s', code, e)
        return 0

    if not records:
        return 0

    async with AsyncSessionLocal() as session:
        affected = 0
        for r in records:
            existing = (await session.execute(
                select(DailyMetricsModel)
                .where(DailyMetricsModel.index_code == r.index_code,
                       DailyMetricsModel.date == r.date)
                .limit(1)
            )).scalar_one_or_none()

            if existing:
                if update_pe and r.pe is not None and existing.pe is None:
                    existing.pe = r.pe
                    existing.pb = r.pb
                    affected += 1
            else:
                session.add(DailyMetricsModel(
                    index_code=r.index_code,
                    date=r.date,
                    close=r.close,
                    pe=r.pe,
                    pb=r.pb,
                    ps=r.ps,
                    dyr=r.dyr,
                    source=r.source,
                ))
                affected += 1
        await session.commit()
    return affected


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

    await run_lixinger_enrich()
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
    await run_lixinger_enrich(is_backfill=True)
    logger.info('=== 开始计算分位数 ===')
    await calc_all()


async def run_fix_pe():
    """对已有价格数据但 PE/PB 为 NULL 的指数补充 PE/PB"""
    logger.info('=== 开始 PE/PB 补充 ===')
    start_date = date(date.today().year - BACKFILL_YEARS, 1, 1)

    async with AsyncSessionLocal() as session:
        indices = (await session.execute(select(Index))).scalars().all()

    for idx in indices:
        logger.info('修复 PE/PB: %s %s', idx.code, idx.name)
        n = await fetch_index(idx.code, idx.market, start_date, update_pe=True)
        logger.info('%s: 更新 %d 条', idx.code, n)

    logger.info('=== PE/PB 补充完成，重算分位数 ===')
    await calc_all()


async def _apply_lixinger_records(records: list) -> int:
    """将一批理杏仁 DailyMetrics 写入 daily_metrics。
    - pe/pb：只填充原为 NULL 的行（保留 akshare 已有数据）
    - ps/dyr：lixinger 独有，有值则直接覆写
    """
    async with AsyncSessionLocal() as session:
        updated = 0
        for r in records:
            existing = (await session.execute(
                select(DailyMetricsModel)
                .where(DailyMetricsModel.index_code == r.index_code,
                       DailyMetricsModel.date == r.date)
                .limit(1)
            )).scalar_one_or_none()

            if not existing:
                continue

            changed = False
            if r.pe is not None and existing.pe is None:
                existing.pe = r.pe
                existing.pb = r.pb
                changed = True
            if r.ps is not None:
                existing.ps = r.ps
                changed = True
            if r.dyr is not None:
                existing.dyr = r.dyr
                changed = True
            if changed:
                updated += 1

        await session.commit()
    return updated


async def run_lixinger_enrich(is_backfill: bool = False, codes: list[str] | None = None):
    """用理杏仁数据补充 daily_metrics 中缺失的 PE/PB（仅 cn 市场）

    is_backfill=True : 逐个指数拉 11 年历史（API 限制：有日期范围时只能传 1 个 code）
    is_backfill=False: 批量拉所有指数最新一条（API 允许最多 100 个 code）
    codes            : 指定指数列表，默认为数据库中全部 cn 市场指数
    """
    if not settings.LIXINGER_TOKEN:
        logger.info('LIXINGER_TOKEN 未配置，跳过理杏仁增强')
        return

    logger.info('=== 开始理杏仁 PE/PB 增强（%s）===', '历史回填' if is_backfill else '每日增量')

    if codes:
        # 使用指定的指数列表
        async with AsyncSessionLocal() as session:
            indices = (await session.execute(
                select(Index).where(Index.market == 'cn', Index.code.in_(codes))
            )).scalars().all()
        logger.info('指定指数：%s', ', '.join(codes))
    else:
        async with AsyncSessionLocal() as session:
            indices = (await session.execute(
                select(Index).where(Index.market == 'cn')
            )).scalars().all()

    lixinger = LixingerProvider()

    if is_backfill:
        # 逐个指数，带完整日期区间
        start_date = date(date.today().year - BACKFILL_YEARS, 1, 1)
        for idx in indices:
            logger.info('理杏仁历史回填 %s %s', idx.code, idx.name)
            try:
                records = lixinger.get_history(idx.code, idx.market, start_date)
            except DataFetchError as e:
                logger.warning('理杏仁 %s: %s', idx.code, e)
                continue
            updated = await _apply_lixinger_records(records)
            logger.info('%s: 理杏仁更新 %d 条 PE/PB', idx.code, updated)
    else:
        # 批量获取最新一条，最多 100 个 code 一次
        batch_codes = [idx.code for idx in indices]
        try:
            records = lixinger.get_latest_batch(batch_codes)
        except DataFetchError as e:
            logger.warning('理杏仁批量增强失败: %s', e)
            return
        updated = await _apply_lixinger_records(records)
        logger.info('理杏仁批量更新 %d 条 PE/PB（%d 个指数）', updated, len(batch_codes))

    logger.info('=== 理杏仁 PE/PB 增强完成 ===')


async def _backfill_one_from_cache(code: str) -> tuple[int, int]:
    """从 lixinger_fundamentals 将单个指数的 pe/pb/ps/dyr 回填到 daily_metrics"""
    from app.models.lixinger_fundamental import LixingerFundamental

    async with AsyncSessionLocal() as session:
        lf_rows = (await session.execute(
            select(LixingerFundamental)
            .where(LixingerFundamental.index_code == code)
            .order_by(LixingerFundamental.date)
        )).scalars().all()

        if not lf_rows:
            return 0, 0

        dm_rows = (await session.execute(
            select(DailyMetricsModel).where(DailyMetricsModel.index_code == code)
        )).scalars().all()
        dm_map = {r.date: r for r in dm_rows}

        updated = inserted = 0

        for lf in lf_rows:
            d = lf.data
            pe_val  = d.get('pe_ttm.mcw')
            pb_val  = d.get('pb.mcw')
            ps_val  = d.get('ps_ttm.mcw')
            dyr_val = d.get('dyr.mcw')
            cp_val  = d.get('cp')

            existing = dm_map.get(lf.date)
            if existing:
                changed = False
                if pe_val is not None and existing.pe is None:
                    existing.pe = float(pe_val)
                    changed = True
                if pb_val is not None and existing.pb is None:
                    existing.pb = float(pb_val)
                    changed = True
                if ps_val is not None and existing.ps is None:
                    existing.ps = float(ps_val)
                    changed = True
                if dyr_val is not None and existing.dyr is None:
                    existing.dyr = float(dyr_val)
                    changed = True
                if changed:
                    updated += 1
            elif cp_val is not None:
                # akshare 无法抓取的指数，用 lixinger 数据建行
                session.add(DailyMetricsModel(
                    index_code=code,
                    date=lf.date,
                    close=float(cp_val),
                    pe=float(pe_val)   if pe_val  is not None else None,
                    pb=float(pb_val)   if pb_val  is not None else None,
                    ps=float(ps_val)   if ps_val  is not None else None,
                    dyr=float(dyr_val) if dyr_val is not None else None,
                    source='lixinger',
                ))
                inserted += 1

        await session.commit()
    return updated, inserted


async def run_backfill_from_lixinger_cache():
    """从 lixinger_fundamentals 缓存表回填 daily_metrics 的 pe/pb/ps/dyr"""
    from app.models.lixinger_fundamental import LixingerFundamental

    logger.info('=== 从 lixinger_fundamentals 缓存回填 daily_metrics ===')

    async with AsyncSessionLocal() as session:
        codes = [r[0] for r in (await session.execute(
            select(LixingerFundamental.index_code).distinct()
        )).all()]

    logger.info('共 %d 个指数有缓存数据', len(codes))
    total_updated = total_inserted = 0

    for code in codes:
        u, i = await _backfill_one_from_cache(code)
        total_updated += u
        total_inserted += i
        logger.info('%s: 更新 %d 条，新增 %d 条', code, u, i)

    logger.info('=== 回填完成：共更新 %d 条，新增 %d 条 ===', total_updated, total_inserted)


async def main_async(mode: str, codes: list[str] | None = None):
    try:
        if mode == 'backfill':
            await run_backfill()
        elif mode == 'fix_pe':
            await run_fix_pe()
        elif mode == 'lixinger_enrich':
            await run_lixinger_enrich(is_backfill=True, codes=codes)
        elif mode == 'backfill_cache':
            await run_backfill_from_lixinger_cache()
        else:
            await run_daily()
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--now', action='store_true', help='立即执行一次后退出')
    parser.add_argument('--backfill', action='store_true', help='历史回填后退出')
    parser.add_argument('--fix-pe', action='store_true', help='补充 PE/PB 为 NULL 的历史记录')
    parser.add_argument('--lixinger-enrich', action='store_true', help='仅运行理杏仁 PE/PB 增强')
    parser.add_argument('--codes', nargs='+', metavar='CODE', help='指定指数代码，配合 --lixinger-enrich 使用')
    args = parser.parse_args()

    if args.backfill:
        asyncio.run(main_async('backfill'))
        return

    if args.fix_pe:
        asyncio.run(main_async('fix_pe'))
        return

    if args.lixinger_enrich:
        asyncio.run(main_async('lixinger_enrich', codes=args.codes))
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
