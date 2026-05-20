from datetime import date
from .base import DataProvider, DailyMetrics, DataFetchError

SOURCE = 'akshare'


class AkshareProvider(DataProvider):
    """A股 / 港股数据源，基于 akshare 库"""

    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        try:
            import akshare as ak  # noqa: F401 — 延迟导入，避免启动时必须安装
            # TODO Phase 2: 按 code/market 调用对应 akshare 接口
            raise NotImplementedError
        except ImportError:
            raise DataFetchError('akshare not installed')
        except NotImplementedError:
            raise DataFetchError(f'akshare provider not yet implemented for {code}')
        except Exception as e:
            raise DataFetchError(f'akshare fetch error for {code}: {e}') from e

    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        try:
            import akshare as ak  # noqa: F401
            raise NotImplementedError
        except ImportError:
            raise DataFetchError('akshare not installed')
        except NotImplementedError:
            raise DataFetchError(f'akshare history not yet implemented for {code}')
        except Exception as e:
            raise DataFetchError(f'akshare history error for {code}: {e}') from e
