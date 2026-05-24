from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.daily_metrics import DailyMetrics as DM
from ...models.index import Index
from ...models.index_stats import IndexStats
from ...schemas.index import ApiResponse
from ...schemas.market import HeadlineCardSchema, MarketOverviewSchema, SectorItemSchema

router = APIRouter()

# 各市场首页展示的宽基指数，顺序即卡片顺序
HEADLINE_CODES: dict[str, list[str]] = {
    'cn': ['000300', '000016', '000905', '000852', '399006', '000688'],
    'hk': [],
    'us': [],
}


def _f2(v) -> float | None:
    return round(float(v), 2) if v is not None else None


def _f4(v) -> float | None:
    return round(float(v), 4) if v is not None else None


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


@router.get('/market/{market}/overview', response_model=ApiResponse[MarketOverviewSchema])
async def get_market_overview(market: str, db: AsyncSession = Depends(get_db)):
    empty = ApiResponse(data=MarketOverviewSchema(
        market=market, temperature=None, updated_at=None,
        headlines=[], sectors=[], series={}, series_dates=[],
    ))

    # 1. 指数主数据
    idx_rows = (await db.execute(
        select(Index).where(Index.market == market)
    )).scalars().all()
    if not idx_rows:
        return empty

    codes = [i.code for i in idx_rows]
    name_map = {i.code: i.name for i in idx_rows}
    sector_map = {i.code: (i.sector or '其他') for i in idx_rows}

    # 2. 分位数缓存
    stats_map = {
        s.index_code: s
        for s in (await db.execute(
            select(IndexStats).where(IndexStats.index_code.in_(codes))
        )).scalars().all()
    }

    # 3. 每个指数最新一条 daily_metrics
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

    # 市场平均温度（PE/PB 分位均值）
    temps = [_temperature(s) for s in stats_map.values()]
    temps = [t for t in temps if t is not None]
    temperature = _f1(sum(temps) / len(temps)) if temps else None

    # 最新数据日期
    max_date = max((dm.date for dm in dm_map.values()), default=None)
    updated_at = max_date.strftime('%Y-%m-%d') if max_date else None

    # 4. 宽基头部卡片
    headline_codes = HEADLINE_CODES.get(market, [])
    headlines = []
    for code in headline_codes:
        if code not in name_map:
            continue
        s = stats_map.get(code)
        dm = dm_map.get(code)
        headlines.append(HeadlineCardSchema(
            code=code,
            name=name_map[code],
            pe=_f2(dm.pe if dm else None),
            pep=_f1(s.pe_percentile if s else None),
            pb=_f4(dm.pb if dm else None),
            pbp=_f1(s.pb_percentile if s else None),
            temperature=_temperature(s),
        ))

    # 5. 行业热力图
    sec_pe: dict[str, list[float]] = defaultdict(list)
    sec_pct: dict[str, list[float]] = defaultdict(list)
    for code in codes:
        sec = sector_map[code]
        dm = dm_map.get(code)
        s = stats_map.get(code)
        if dm and dm.pe is not None:
            sec_pe[sec].append(float(dm.pe))
        if s and s.pe_percentile is not None:
            sec_pct[sec].append(float(s.pe_percentile))

    sectors = [
        SectorItemSchema(
            name=sec,
            pe=_f2(sum(pes) / len(pes)) if pes else None,
            pct=_f1(sum(sec_pct.get(sec, [])) / len(sec_pct[sec]) * 100)
                if sec_pct.get(sec) else None,
        )
        for sec, pes in sec_pe.items()
    ]
    sectors.sort(key=lambda s: s.pct or 0)

    # 6. PE 走势折线（以沪深300日期为参考轴，宽基指数各自对齐）
    ref_code = next(
        (c for c in headline_codes if c in name_map and dm_map.get(c)), None
    )
    series: dict[str, list[float | None]] = {}
    series_dates: list[str] = []

    if ref_code:
        pe_rows = (await db.execute(
            select(DM.index_code, DM.date, DM.pe)
            .where(DM.index_code.in_(headline_codes))
            .order_by(DM.date)
        )).all()

        pe_by_code: dict[str, dict] = defaultdict(dict)
        for row in pe_rows:
            if row.pe is not None:
                pe_by_code[row.index_code][row.date] = float(row.pe)

        ref_dates = sorted(pe_by_code.get(ref_code, {}).keys())
        series_dates = [d.strftime('%Y-%m-%d') for d in ref_dates]

        for code in headline_codes:
            if code not in name_map or not pe_by_code.get(code):
                continue
            pe_map = pe_by_code[code]
            values: list[float | None] = [pe_map.get(d) for d in ref_dates]
            if any(v is not None for v in values):
                series[name_map[code]] = values

    return ApiResponse(data=MarketOverviewSchema(
        market=market,
        temperature=temperature,
        updated_at=updated_at,
        headlines=headlines,
        sectors=sectors,
        series=series,
        series_dates=series_dates,
    ))
