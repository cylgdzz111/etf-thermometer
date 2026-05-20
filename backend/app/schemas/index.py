from datetime import date, datetime
from pydantic import BaseModel


class IndexRowSchema(BaseModel):
    code: str
    market: str
    name: str
    sector: str | None
    close: float | None
    chg: float | None
    w52: float | None
    peak_dist: float | None
    pe: float | None
    pep: float | None
    pb: float | None
    pbp: float | None
    temperature: float | None


class IndexDetailSchema(IndexRowSchema):
    pe_min: float | None
    pe_max: float | None
    pe_avg: float | None
    pb_min: float | None
    pb_max: float | None
    pb_avg: float | None
    total_ret: float | None
    drawdown: float | None


class IndexHistorySchema(BaseModel):
    price: list[float]
    pe: list[float]
    dates: list[date]


class ApiResponse[T](BaseModel):
    data: T
    updated_at: datetime | None = None
