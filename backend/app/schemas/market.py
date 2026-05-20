from datetime import datetime
from pydantic import BaseModel


class HeadlineCardSchema(BaseModel):
    name: str
    pe: float | None
    pep: float | None
    pb: float | None
    pbp: float | None


class SectorItemSchema(BaseModel):
    name: str
    pe: float | None
    pct: float | None
    chg: float | None


class MarketOverviewSchema(BaseModel):
    market: str
    temperature: float | None
    updated_at: datetime | None
    headlines: list[HeadlineCardSchema]
    sectors: list[SectorItemSchema]
    series: dict[str, list[float]]
