from collections import defaultdict
from datetime import date, timedelta

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.daily_metrics import DailyMetrics as DM
from ...models.index import Index
from ...models.index_stats import IndexStats
from ...schemas.index import (
    ApiResponse,
    IndexDetailSchema,
    IndexHistorySchema,
    IndexRowSchema,
    RangeStats,
)

router = APIRouter()

SPARKLINE_DAYS = 60
DIST_BINS = 20
MIN_STAT_DAYS = 20   # 区间内至少有这么多非空值才计算分位线


def _f2(v) -> float | None:
    return round(float(v), 2) if v is not None else None

def _f4(v) -> float | None:
    return round(float(v), 4) if v is not None else None

def _f6(v) -> float | None:
    return round(float(v), 6) if v is not None else None

def _f1(v) -> float | None:
    return round(float(v), 1) if v is not None else None


def _temperature(s) -> float | None:
    """PE/PB 分位均值，作为综合温度；temperature 字段已从 index_stats 移除。"""
    if s is None:
        return None
    pe, pb = s.pe_percentile, s.pb_percentile
    if pe is not None and pb is not None:
        return round((float(pe) + float(pb)) / 2, 1)
    return None


def _range_stats(series: list[float | None], current: float | None) -> RangeStats:
    """从当前区间的时间序列计算 p30/p50/p80 及最新值的区间分位。"""
    vals = np.array([v for v in series if v is not None], dtype=float)
    if len(vals) < MIN_STAT_DAYS or current is None:
        return RangeStats()
    return RangeStats(
        p30=round(float(np.percentile(vals, 30)), 6),
        p50=round(float(np.percentile(vals, 50)), 6),
        p80=round(float(np.percentile(vals, 80)), 6),
        pct=round(float(np.sum(vals <= current) / len(vals) * 100), 2),
    )


def _make_dist(values: list[float]) -> tuple[list[int], float | None, float | None]:
    if not values:
        return [], None, None
    mn, mx = min(values), max(values)
    if mn == mx:
        return [len(values)] + [0] * (DIST_BINS - 1), mn, mx
    bucket = (mx - mn) / DIST_BINS
    counts = [0] * DIST_BINS
    for v in values:
        counts[min(int((v - mn) / bucket), DIST_BINS - 1)] += 1
    return counts, mn, mx


@router.get('/indices', response_model=ApiResponse[list[IndexRowSchema]])
async def list_indices(
    market: str = Query('cn'),
    sector: str | None = Query(None),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Index).where(Index.market == market)
    if sector:
        stmt = stmt.where(Index.sector == sector)
    if q:
        stmt = stmt.where(or_(Index.name.contains(q), Index.code.contains(q)))
    idx_rows = (await db.execute(stmt)).scalars().all()

    if not idx_rows:
        return ApiResponse(data=[])

    codes = [i.code for i in idx_rows]

    stats_map = {
        s.index_code: s
        for s in (await db.execute(
            select(IndexStats).where(IndexStats.index_code.in_(codes))
        )).scalars().all()
    }

    latest_subq = (
        select(DM.index_code, func.max(DM.date).label('max_date'))
        .where(DM.index_code.in_(codes))
        .group_by(DM.index_code)
        .subquery()
    )
    dm_map = {
        r.index_code: r
        for r in (await db.execute(
            select(DM).join(latest_subq, and_(
                DM.index_code == latest_subq.c.index_code,
                DM.date == latest_subq.c.max_date,
            ))
        )).scalars().all()
    }

    spark_raw: dict[str, list[float]] = defaultdict(list)
    for row in (await db.execute(
        select(DM.index_code, DM.date, DM.close)
        .where(DM.index_code.in_(codes), DM.close.isnot(None))
        .order_by(DM.index_code, DM.date.desc())
    )).all():
        if len(spark_raw[row.index_code]) < SPARKLINE_DAYS:
            spark_raw[row.index_code].append(float(row.close))
    spark_map = {k: list(reversed(v)) for k, v in spark_raw.items()}

    result = []
    for idx in idx_rows:
        code = idx.code
        dm = dm_map.get(code)
        s = stats_map.get(code)
        result.append(IndexRowSchema(
            code=code,
            market=idx.market,
            name=idx.name,
            sector=idx.sector,
            close=_f2(dm.close if dm else None),
            pe=_f2(dm.pe if dm else None),
            pep=_f1(s.pe_percentile if s else None),
            pb=_f4(dm.pb if dm else None),
            pbp=_f1(s.pb_percentile if s else None),
            temperature=_temperature(s),
            sparkline=spark_map.get(code, []),
        ))

    return ApiResponse(data=result)


@router.get('/indices/{code}', response_model=ApiResponse[IndexDetailSchema])
async def get_index_detail(code: str, db: AsyncSession = Depends(get_db)):
    idx = (await db.execute(
        select(Index).where(Index.code == code)
    )).scalar_one_or_none()
    if not idx:
        raise HTTPException(status_code=404, detail='Index not found')

    s = (await db.execute(
        select(IndexStats).where(IndexStats.index_code == code)
    )).scalar_one_or_none()

    latest_date = (await db.execute(
        select(func.max(DM.date)).where(DM.index_code == code)
    )).scalar_one_or_none()

    dm = None
    if latest_date:
        dm = (await db.execute(
            select(DM).where(DM.index_code == code, DM.date == latest_date)
        )).scalar_one_or_none()

    hist_rows = (await db.execute(
        select(DM.pe, DM.pb, DM.ps, DM.dyr)
        .where(DM.index_code == code)
        .order_by(DM.date)
    )).all()

    pe_vals  = [float(r.pe)  for r in hist_rows if r.pe  is not None]
    pb_vals  = [float(r.pb)  for r in hist_rows if r.pb  is not None]
    ps_vals  = [float(r.ps)  for r in hist_rows if r.ps  is not None]
    dyr_vals = [float(r.dyr) for r in hist_rows if r.dyr is not None]

    pe_dist,  pe_dist_min,  pe_dist_max  = _make_dist(pe_vals)
    pb_dist,  pb_dist_min,  pb_dist_max  = _make_dist(pb_vals)
    ps_dist,  ps_dist_min,  ps_dist_max  = _make_dist(ps_vals)
    dyr_dist, dyr_dist_min, dyr_dist_max = _make_dist(dyr_vals)

    return ApiResponse(data=IndexDetailSchema(
        code=code,
        market=idx.market,
        name=idx.name,
        sector=idx.sector,
        close=_f2(dm.close if dm else None),
        pe=_f2(dm.pe if dm else None),
        pep=_f1(s.pe_percentile if s else None),
        pb=_f4(dm.pb if dm else None),
        pbp=_f1(s.pb_percentile if s else None),
        temperature=_temperature(s),
        sparkline=[],
        pe_min=_f2(s.pe_min if s else None),
        pe_max=_f2(s.pe_max if s else None),
        pe_avg=_f2(s.pe_avg if s else None),
        pe_dist=pe_dist,
        pe_dist_min=_f2(pe_dist_min),
        pe_dist_max=_f2(pe_dist_max),
        pb_min=_f4(s.pb_min if s else None),
        pb_max=_f4(s.pb_max if s else None),
        pb_avg=_f4(s.pb_avg if s else None),
        pb_dist=pb_dist,
        pb_dist_min=_f4(pb_dist_min),
        pb_dist_max=_f4(pb_dist_max),
        ps=_f4(dm.ps if dm else None),
        psp=_f1(s.ps_percentile if s else None),
        ps_min=_f4(s.ps_min if s else None),
        ps_max=_f4(s.ps_max if s else None),
        ps_avg=_f4(s.ps_avg if s else None),
        ps_dist=ps_dist,
        ps_dist_min=_f4(ps_dist_min),
        ps_dist_max=_f4(ps_dist_max),
        dyr=_f6(dm.dyr if dm else None),
        dyrp=_f1(s.dyr_percentile if s else None),
        dyr_min=_f6(s.dyr_min if s else None),
        dyr_max=_f6(s.dyr_max if s else None),
        dyr_avg=_f6(s.dyr_avg if s else None),
        dyr_dist=dyr_dist,
        dyr_dist_min=_f6(dyr_dist_min),
        dyr_dist_max=_f6(dyr_dist_max),
    ))


@router.get('/indices/{code}/history', response_model=ApiResponse[IndexHistorySchema])
async def get_index_history(
    code: str,
    range: str = Query('5y', pattern='^(1y|3y|5y|10y|all)$'),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    if range == '1y':
        start = today - timedelta(days=365)
    elif range == '3y':
        start = today - timedelta(days=365 * 3)
    elif range == '5y':
        start = today - timedelta(days=365 * 5)
    elif range == '10y':
        start = today - timedelta(days=365 * 10)
    else:
        start = date(2000, 1, 1)

    rows = (await db.execute(
        select(DM.date, DM.close, DM.pe, DM.pb, DM.ps, DM.dyr)
        .where(DM.index_code == code, DM.date >= start)
        .order_by(DM.date)
    )).all()

    price_series = [float(r.close) if r.close is not None else None for r in rows]
    pe_series    = [float(r.pe)    if r.pe    is not None else None for r in rows]
    pb_series    = [float(r.pb)    if r.pb    is not None else None for r in rows]
    ps_series    = [float(r.ps)    if r.ps    is not None else None for r in rows]
    dyr_series   = [float(r.dyr)   if r.dyr   is not None else None for r in rows]

    # 取各指标最新非空值作为「当前值」，用于计算区间分位
    def _last(s: list) -> float | None:
        for v in reversed(s):
            if v is not None:
                return v
        return None

    return ApiResponse(data=IndexHistorySchema(
        dates=[r.date.strftime('%Y-%m-%d') for r in rows],
        price=price_series,
        pe=pe_series,
        pb=pb_series,
        ps=ps_series,
        dyr=dyr_series,
        pe_stats  =_range_stats(pe_series,  _last(pe_series)),
        pb_stats  =_range_stats(pb_series,  _last(pb_series)),
        ps_stats  =_range_stats(ps_series,  _last(ps_series)),
        dyr_stats =_range_stats(dyr_series, _last(dyr_series)),
    ))
