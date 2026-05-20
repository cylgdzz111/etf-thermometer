from pydantic import BaseModel


class HeadlineCardSchema(BaseModel):
    code: str
    name: str
    pe: float | None
    pep: float | None
    pb: float | None
    pbp: float | None
    temperature: float | None


class SectorItemSchema(BaseModel):
    name: str
    pe: float | None
    pct: float | None   # 行业平均 PE 分位数（0-100）


class MarketOverviewSchema(BaseModel):
    market: str
    temperature: float | None
    updated_at: str | None
    headlines: list[HeadlineCardSchema]
    sectors: list[SectorItemSchema]
    series: dict[str, list[float | None]]   # {指数名: [pe值...]}，含null缺口
    series_dates: list[str]                 # 共享日期轴（ISO 格式）
