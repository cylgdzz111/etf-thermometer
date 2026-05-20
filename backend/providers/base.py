from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class DailyMetrics:
    index_code: str
    date: date
    close: float | None
    pe: float | None
    pb: float | None
    source: str


class DataFetchError(Exception):
    pass


class DataProvider(ABC):
    @abstractmethod
    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        """获取单个指数最新一日数据"""
        ...

    @abstractmethod
    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        """获取指定起始日期至今的历史数据"""
        ...
