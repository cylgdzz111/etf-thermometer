from datetime import datetime
from pydantic import BaseModel


class IndexRowSchema(BaseModel):
    code: str
    market: str
    name: str
    sector: str | None
    close: float | None
    pe: float | None
    pep: float | None
    pb: float | None
    pbp: float | None
    temperature: float | None
    sparkline: list[float] = []


class IndexDetailSchema(IndexRowSchema):
    # PE
    pe_min: float | None
    pe_max: float | None
    pe_avg: float | None
    pe_dist: list[int] = []
    pe_dist_min: float | None = None
    pe_dist_max: float | None = None

    # PB
    pb_min: float | None
    pb_max: float | None
    pb_avg: float | None
    pb_dist: list[int] = []
    pb_dist_min: float | None = None
    pb_dist_max: float | None = None

    # PS
    ps: float | None
    psp: float | None
    ps_min: float | None
    ps_max: float | None
    ps_avg: float | None
    ps_dist: list[int] = []
    ps_dist_min: float | None = None
    ps_dist_max: float | None = None

    # DYR
    dyr: float | None
    dyrp: float | None
    dyr_min: float | None
    dyr_max: float | None
    dyr_avg: float | None
    dyr_dist: list[int] = []
    dyr_dist_min: float | None = None
    dyr_dist_max: float | None = None


class RangeStats(BaseModel):
    """单个指标在某时间区间内的统计，随 history 接口返回"""
    p30: float | None = None
    p50: float | None = None
    p80: float | None = None
    pct: float | None = None   # 最新值在该区间的分位（0–100）


class IndexHistorySchema(BaseModel):
    dates: list[str]
    price: list[float | None]
    pe:    list[float | None]
    pb:    list[float | None]
    ps:    list[float | None]
    dyr:   list[float | None]

    # 各指标在本次请求区间内动态计算的分位线 + 区间内分位
    pe_stats:  RangeStats = RangeStats()
    pb_stats:  RangeStats = RangeStats()
    ps_stats:  RangeStats = RangeStats()
    dyr_stats: RangeStats = RangeStats()


class ApiResponse[T](BaseModel):
    data: T
    updated_at: datetime | None = None
