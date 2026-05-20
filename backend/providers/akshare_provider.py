"""
AkshareProvider — A 股 / 港股数据源

PE/PB 历史：乐咕乐股 (stock_index_pe_lg / stock_index_pb_lg)
           仅支持少数主流宽基，其余留空
价格历史：stock_zh_index_daily (全量，按交易所前缀)
"""
import logging
import time
from datetime import date, timedelta
from typing import Callable, TypeVar

import pandas as pd

T = TypeVar('T')

from .base import DataProvider, DailyMetrics, DataFetchError

logger = logging.getLogger(__name__)

# 乐咕乐股 PE/PB 接口支持的指数（code → legulegu symbol）
LEGULEGU_PE_SYMBOLS: dict[str, str] = {
    '000016': '上证50',
    '000300': '沪深300',
    '000905': '中证500',
}

# 交易所前缀映射（stock_zh_index_daily 接口）
# 000xxx / 688xxx → sh；399xxx → sz；特殊代码手动映射
EXCHANGE_PREFIX: dict[str, str] = {
    'h30590': 'sz',   # 华证机器人，深交所发布
}


def _retry(fn: Callable[[], T], retries: int = 3, delay: float = 5.0) -> T:
    """简单重试装饰器，指数退避"""
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = delay * (2 ** attempt)
            logger.warning('重试 %d/%d，等待 %.0fs: %s', attempt + 1, retries, wait, e)
            time.sleep(wait)
    raise RuntimeError('unreachable')


def _exchange_prefix(code: str) -> str:
    if code in EXCHANGE_PREFIX:
        return EXCHANGE_PREFIX[code]
    if code.startswith('399') or code.startswith('159'):
        return 'sz'
    return 'sh'


def _fetch_price_history(code: str) -> pd.DataFrame:
    """返回 DataFrame: date(date), close(float)"""
    import akshare as ak
    symbol = f'{_exchange_prefix(code)}{code}'
    df = ak.stock_zh_index_daily(symbol=symbol)
    df = df[['date', 'close']].copy()
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.dropna(subset=['close'])
    return df.set_index('date')


def _fetch_legulegu_pe(lg_symbol: str) -> pd.DataFrame:
    """返回 DataFrame: date(date), pe(float)"""
    import akshare as ak
    df = ak.stock_index_pe_lg(symbol=lg_symbol)
    df = df.rename(columns={'日期': 'date', '滚动市盈率': 'pe'})
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[['date', 'pe']].dropna()
    return df.set_index('date')


def _fetch_legulegu_pb(lg_symbol: str) -> pd.DataFrame:
    """返回 DataFrame: date(date), pb(float)"""
    import akshare as ak
    df = ak.stock_index_pb_lg(symbol=lg_symbol)
    df = df.rename(columns={'日期': 'date', '市净率': 'pb'})
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[['date', 'pb']].dropna()
    return df.set_index('date')


class AkshareProvider(DataProvider):
    """A股数据 Provider，基于 akshare 库"""

    SOURCE = 'akshare'

    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        try:
            import akshare  # noqa: F401 — 确认已安装
        except ImportError:
            raise DataFetchError('akshare not installed. Run: pip install akshare')

        try:
            price_df = _retry(lambda: _fetch_price_history(code))
        except Exception as e:
            raise DataFetchError(f'价格历史抓取失败 {code}: {e}') from e

        # 合并 PE/PB（仅支持的指数有数据）
        pe_df: pd.DataFrame | None = None
        pb_df: pd.DataFrame | None = None
        lg_symbol = LEGULEGU_PE_SYMBOLS.get(code)
        if lg_symbol:
            try:
                pe_df = _retry(lambda: _fetch_legulegu_pe(lg_symbol))
                time.sleep(1.0)   # 避免乐咕乐股限速
                pb_df = _retry(lambda: _fetch_legulegu_pb(lg_symbol))
            except Exception as e:
                logger.warning('PE/PB 数据抓取失败 %s (%s): %s，将以 NULL 写入', code, lg_symbol, e)
                pe_df = pb_df = None

        results: list[DailyMetrics] = []
        for d, row in price_df.iterrows():
            if d < start_date:
                continue
            pe = float(pe_df.at[d, 'pe']) if (pe_df is not None and d in pe_df.index) else None
            pb = float(pb_df.at[d, 'pb']) if (pb_df is not None and d in pb_df.index) else None
            results.append(DailyMetrics(
                index_code=code,
                date=d,
                close=float(row['close']),
                pe=pe,
                pb=pb,
                ps=None,
                dyr=None,
                source=self.SOURCE,
            ))
        return results

    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        # 取近 5 天历史，返回最新一条
        start = date.today() - timedelta(days=5)
        history = self.get_history(code, market, start)
        if not history:
            raise DataFetchError(f'无法获取 {code} 最新数据')
        return sorted(history, key=lambda x: x.date)[-1]
