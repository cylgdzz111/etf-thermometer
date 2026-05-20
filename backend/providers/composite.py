import logging
from datetime import date
from .base import DataProvider, DailyMetrics, DataFetchError
from .akshare_provider import AkshareProvider
from .yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)

# 按市场分配数据源，列表顺序即优先级，前一个失败时 fallback 到下一个
ROUTING: dict[str, list[type[DataProvider]]] = {
    'cn': [AkshareProvider],
    'hk': [AkshareProvider],
    'us': [YFinanceProvider],
}


class CompositeProvider(DataProvider):
    """路由 + Fallback 组合 Provider"""

    def _providers(self, market: str) -> list[DataProvider]:
        klasses = ROUTING.get(market, [])
        return [klass() for klass in klasses]

    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        errors: list[str] = []
        for p in self._providers(market):
            try:
                return p.get_daily_metrics(code, market)
            except DataFetchError as e:
                logger.warning('Provider %s failed for %s: %s', type(p).__name__, code, e)
                errors.append(str(e))
        raise DataFetchError(f'All providers failed for {code}: {"; ".join(errors)}')

    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        errors: list[str] = []
        for p in self._providers(market):
            try:
                return p.get_history(code, market, start_date)
            except DataFetchError as e:
                logger.warning('Provider %s history failed for %s: %s', type(p).__name__, code, e)
                errors.append(str(e))
        raise DataFetchError(f'All providers failed history for {code}: {"; ".join(errors)}')
