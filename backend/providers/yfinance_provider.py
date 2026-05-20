from datetime import date
from .base import DataProvider, DailyMetrics, DataFetchError

SOURCE = 'yfinance'


class YFinanceProvider(DataProvider):
    """美股数据源，基于 yfinance 库"""

    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        try:
            import yfinance as yf  # noqa: F401 — 延迟导入
            raise NotImplementedError
        except ImportError:
            raise DataFetchError('yfinance not installed')
        except NotImplementedError:
            raise DataFetchError(f'yfinance provider not yet implemented for {code}')
        except Exception as e:
            raise DataFetchError(f'yfinance fetch error for {code}: {e}') from e

    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        try:
            import yfinance as yf  # noqa: F401
            raise NotImplementedError
        except ImportError:
            raise DataFetchError('yfinance not installed')
        except NotImplementedError:
            raise DataFetchError(f'yfinance history not yet implemented for {code}')
        except Exception as e:
            raise DataFetchError(f'yfinance history error for {code}: {e}') from e
