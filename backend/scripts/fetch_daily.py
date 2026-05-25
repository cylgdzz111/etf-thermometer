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
# from providers.composite import CompositeProvider  # akshare 暂时停用
from providers.lixinger_provider import LixingerProvider
from providers.base import DataFetchError
from scripts.calc_stats import calc_all

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger('fetch_daily')

# provider = CompositeProvider()  # akshare 暂时停用


# ── akshare 相关函数暂时停用，恢复时取消注释并重新启用 CompositeProvider ──────
# async def fetch_index(code, market, start_date, update_pe=False): ...
# async def get_latest_date(code): ...
# async def run_fix_pe(): ...
# ─────────────────────────────────────────────────────────────────────────────


async def run_daily():
    """每日增量更新：通过理杏仁批量拉取最新一条数据"""
    logger.info('=== 开始每日增量更新 ===')
    await run_lixinger_enrich()
    logger.info('=== 开始计算分位数 ===')
    await calc_all()


async def run_backfill():
    """历史回填：通过理杏仁逐个指数拉取近 10 年历史数据"""
    logger.info('=== 开始历史回填（近 10 年）===')
    await run_lixinger_enrich(is_backfill=True)
    logger.info('=== 开始计算分位数 ===')
    await calc_all()


async def _apply_lixinger_records(records: list) -> int:
    """将一批理杏仁 DailyMetrics 写入 daily_metrics。
    - 行不存在且有收盘价（cp）：直接插入（用于港股等 akshare 无法抓取的指数）
    - 行已存在：pe/pb 只填充 NULL，ps/dyr 有值则覆写
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
                # akshare 无数据的指数（如港股），用理杏仁数据直接建行
                if r.close is not None:
                    session.add(DailyMetricsModel(
                        index_code=r.index_code,
                        date=r.date,
                        close=r.close,
                        pe=r.pe,
                        pb=r.pb,
                        ps=r.ps,
                        dyr=r.dyr,
                        source='lixinger',
                    ))
                    updated += 1
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


async def _get_outdated_indices(indices: list) -> list:
    """返回需要更新的指数：latest pe 日期落后于当前最新交易日的。

    以已有数据中最新的那天为"参照日期"，自动适配工作日/非交易日：
    - 工作日重跑：第一批已更新的指数将参照日期推到今天，剩余未更新的被返回
    - 非交易日重跑：参照日期 = 上一个交易日，已有该日数据的全部跳过
    """
    if not indices:
        return []
    codes = [idx.code for idx in indices]
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(DailyMetricsModel.index_code,
                   func.max(DailyMetricsModel.date).label('latest'))
            .where(DailyMetricsModel.index_code.in_(codes),
                   DailyMetricsModel.pe.isnot(None))
            .group_by(DailyMetricsModel.index_code)
        )).all()
    latest_map = {r.index_code: r.latest for r in rows}

    all_dates = [d for d in latest_map.values() if d]
    ref_date = max(all_dates) if all_dates else None

    need, skip = [], []
    for idx in indices:
        d = latest_map.get(idx.code)
        if ref_date and d and d >= ref_date:
            skip.append(idx.code)
        else:
            need.append(idx)

    if skip:
        logger.info('参照日期 %s，已是最新跳过 %d 个：%s', ref_date, len(skip), ', '.join(skip))
    return need


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

    # 理杏仁支持 cn / hk 两个市场
    SUPPORTED_MARKETS = ('cn', 'hk')

    if codes:
        # 使用指定的指数列表（指定时不限 is_active，方便单独回填）
        async with AsyncSessionLocal() as session:
            indices = (await session.execute(
                select(Index).where(
                    Index.market.in_(SUPPORTED_MARKETS),
                    Index.code.in_(codes),
                )
            )).scalars().all()
        logger.info('指定指数：%s', ', '.join(codes))
    else:
        async with AsyncSessionLocal() as session:
            indices = (await session.execute(
                select(Index).where(
                    Index.market.in_(SUPPORTED_MARKETS),
                    Index.is_active == True,  # noqa: E712
                )
            )).scalars().all()

    lixinger = LixingerProvider()

    if is_backfill:
        # 逐个指数，带完整日期区间（理杏仁限制最多10年）
        today = date.today()
        start_date = date(today.year - 10, today.month, today.day)
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
        # 批量获取最新一条：先过滤已有最新数据的指数，避免重跑浪费 API 调用
        total = len(indices)
        indices = await _get_outdated_indices(list(indices))
        if not indices:
            logger.info('所有 %d 个指数已是最新，跳过理杏仁请求', total)
            return

        code_market_pairs = [(idx.code, idx.market) for idx in indices]
        logger.info('共 %d 个指数需要更新（已跳过 %d 个）', len(indices), total - len(indices))
        try:
            records = lixinger.get_latest_batch(code_market_pairs)
        except DataFetchError as e:
            logger.warning('理杏仁批量增强失败: %s', e)
            return
        updated = await _apply_lixinger_records(records)
        logger.info('理杏仁批量更新 %d 条 PE/PB（%d 个指数）', updated, len(code_market_pairs))

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
        # elif mode == 'fix_pe':        # akshare 暂时停用
        #     await run_fix_pe()
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
    # parser.add_argument('--fix-pe', ...)  # akshare 暂时停用
    parser.add_argument('--lixinger-enrich', action='store_true', help='仅运行理杏仁 PE/PB 增强')
    parser.add_argument('--codes', nargs='+', metavar='CODE', help='指定指数代码，配合 --lixinger-enrich 使用')
    args = parser.parse_args()

    if args.backfill:
        asyncio.run(main_async('backfill'))
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
