"""
LixingerProvider — 理杏仁基本面数据源

仅提供 PE/PB 等估值指标，不提供价格数据。
用于在 akshare 抓取价格后，对 daily_metrics 进行 PE/PB 增强。
API:
  A 股: POST https://open.lixinger.com/api/cn/index/fundamental
  港股: POST https://open.lixinger.com/api/hk/index/fundamental

API 调用限制：
  - 传 startDate/endDate（历史区间）：每次只能传 1 个 stockCode
  - 不传日期（获取最新一条）：每次最多传 100 个 stockCode
"""
import logging
import time
from datetime import date
from typing import Any

import requests

from .base import DataProvider, DailyMetrics, DataFetchError

logger = logging.getLogger(__name__)

LIXINGER_APIS: dict[str, str] = {
    'cn': 'https://open.lixinger.com/api/cn/index/fundamental',
    'hk': 'https://open.lixinger.com/api/hk/index/fundamental',
}
BATCH_SIZE = 100  # 不传日期时最大批量大小

# ── A 股完整指标列表 ──────────────────────────────────────────────────────
CN_METRICS_LIST = [
    # 当前值：4 指标 × 5 metricsType
    'pe_ttm.mcw', 'pe_ttm.ew', 'pe_ttm.ewpvo', 'pe_ttm.avg', 'pe_ttm.median',
    'pb.mcw',     'pb.ew',     'pb.ewpvo',     'pb.avg',     'pb.median',
    'ps_ttm.mcw', 'ps_ttm.ew', 'ps_ttm.ewpvo', 'ps_ttm.avg', 'ps_ttm.median',
    'dyr.mcw',    'dyr.ew',    'dyr.ewpvo',    'dyr.avg',    'dyr.median',

    # pe_ttm 历史区间统计
    'pe_ttm.y10.mcw.cvpos', 'pe_ttm.y10.mcw.cv', 'pe_ttm.y10.mcw.minv', 'pe_ttm.y10.mcw.maxv', 'pe_ttm.y10.mcw.avgv',
    'pe_ttm.y5.mcw.cvpos',  'pe_ttm.y5.mcw.cv',  'pe_ttm.y5.mcw.minv',  'pe_ttm.y5.mcw.maxv',  'pe_ttm.y5.mcw.avgv',
    'pe_ttm.y3.mcw.cvpos',  'pe_ttm.y3.mcw.cv',  'pe_ttm.y3.mcw.minv',  'pe_ttm.y3.mcw.maxv',
    'pe_ttm.y1.mcw.cvpos',  'pe_ttm.y1.mcw.cv',
    'pe_ttm.y10.ew.cvpos',  'pe_ttm.y10.ew.cv',  'pe_ttm.y10.ew.minv',  'pe_ttm.y10.ew.maxv',
    'pe_ttm.y5.ew.cvpos',   'pe_ttm.y5.ew.cv',
    'pe_ttm.y3.ew.cvpos',

    # pb 历史区间统计
    'pb.y10.mcw.cvpos', 'pb.y10.mcw.cv', 'pb.y10.mcw.minv', 'pb.y10.mcw.maxv', 'pb.y10.mcw.avgv',
    'pb.y5.mcw.cvpos',  'pb.y5.mcw.cv',  'pb.y5.mcw.minv',  'pb.y5.mcw.maxv',
    'pb.y3.mcw.cvpos',  'pb.y3.mcw.cv',
    'pb.y1.mcw.cvpos',
    'pb.y10.ew.cvpos',  'pb.y10.ew.cv',
    'pb.y5.ew.cvpos',

    # ps_ttm 历史区间统计
    'ps_ttm.y10.mcw.cvpos', 'ps_ttm.y10.mcw.cv', 'ps_ttm.y10.mcw.minv', 'ps_ttm.y10.mcw.maxv',
    'ps_ttm.y5.mcw.cvpos',  'ps_ttm.y5.mcw.cv',
    'ps_ttm.y10.ew.cvpos',

    # dyr 历史区间统计
    'dyr.y10.mcw.cvpos', 'dyr.y10.mcw.cv', 'dyr.y10.mcw.minv', 'dyr.y10.mcw.maxv',
    'dyr.y5.mcw.cvpos',  'dyr.y5.mcw.cv',
    'dyr.y10.ew.cvpos',

    # 行情指标
    'cp', 'cpc', 'r_cp', 'mc', 'cmc', 'ecmc', 'tv', 'ta',
]

# ── 港股精简指标列表 ──────────────────────────────────────────────────────
# 只取写入 daily_metrics 所需的核心字段，分位数由 calc_stats 自行计算
HK_METRICS_LIST = [
    'pe_ttm.mcw',   # → daily_metrics.pe
    'pb.mcw',       # → daily_metrics.pb
    'ps_ttm.mcw',   # → daily_metrics.ps
    'dyr.mcw',      # → daily_metrics.dyr
    'cp',           # → daily_metrics.close
    'cpc',          # 涨跌幅
    'mc',           # 总市值
    'tv',           # 成交量
    'ta',           # 成交金额
]

# 按市场索引，方便取用
METRICS_BY_MARKET: dict[str, list[str]] = {
    'cn': CN_METRICS_LIST,
    'hk': HK_METRICS_LIST,
}


HEADERS = {'Accept-Encoding': 'gzip', 'Content-Type': 'application/json'}

def _post_with_retry(url: str, payload: dict, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, headers=HEADERS, timeout=60)
            if not resp.ok:
                logger.error('理杏仁 HTTP %s，响应: %s', resp.status_code, resp.text[:300])
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 5.0 * (2 ** attempt)
            logger.warning('理杏仁请求重试 %d/%d，%.0fs 后重试: %s', attempt + 1, retries, wait, e)
            time.sleep(wait)
    raise RuntimeError('unreachable')


def _parse_records(raw: list[dict[str, Any]]) -> list[DailyMetrics]:
    """将 API 原始记录解析为 DailyMetrics 列表"""
    results: list[DailyMetrics] = []
    for r in raw:
        d_str = r.get('date', '')
        code = r.get('stockCode', '')
        if not d_str or not code:
            continue
        try:
            d = date.fromisoformat(d_str[:10])
        except ValueError:
            continue

        pe_val  = r.get('pe_ttm.mcw')
        pb_val  = r.get('pb.mcw')
        ps_val  = r.get('ps_ttm.mcw')
        dyr_val = r.get('dyr.mcw')
        cp_val  = r.get('cp')
        results.append(DailyMetrics(
            index_code=code,
            date=d,
            close=float(cp_val)  if cp_val  is not None else None,
            pe=float(pe_val)     if pe_val  is not None else None,
            pb=float(pb_val)     if pb_val  is not None else None,
            ps=float(ps_val)     if ps_val  is not None else None,
            dyr=float(dyr_val)   if dyr_val is not None else None,
            source='lixinger',
        ))
    return results


class LixingerProvider(DataProvider):
    """理杏仁基本面数据 Provider，仅提供 PE/PB 等估值指标"""

    SOURCE = 'lixinger'

    def __init__(self):
        from app.core.config import settings
        self._token = settings.LIXINGER_TOKEN

    def _require_token(self) -> None:
        if not self._token:
            raise DataFetchError('LIXINGER_TOKEN 未配置')

    def _api_url(self, market: str) -> str:
        url = LIXINGER_APIS.get(market)
        if not url:
            raise DataFetchError(f'理杏仁不支持市场: {market}，可选: {list(LIXINGER_APIS)}')
        return url

    # ------------------------------------------------------------------
    # 历史区间抓取：只传 1 个 stockCode，带 startDate/endDate
    # ------------------------------------------------------------------
    def _fetch_range(self, code: str, market: str, start_date: date, end_date: date | None = None) -> list[dict[str, Any]]:
        self._require_token()
        payload: dict[str, Any] = {
            'token': self._token,
            'stockCodes': [code],
            'startDate': start_date.strftime('%Y-%m-%d'),
            'metricsList': METRICS_BY_MARKET.get(market, CN_METRICS_LIST),
        }
        if end_date:
            payload['endDate'] = end_date.strftime('%Y-%m-%d')

        result = _post_with_retry(self._api_url(market), payload)
        if result.get('code') != 1:
            raise DataFetchError(f'理杏仁 API 错误 {code}: {result.get("message")}')
        return result.get('data', [])

    # ------------------------------------------------------------------
    # 批量最新抓取：不传日期，最多 100 个 stockCode（同一市场）
    # ------------------------------------------------------------------
    def _fetch_latest_batch(self, codes: list[str], market: str, fetch_date: date | None = None) -> list[dict[str, Any]]:
        """批量获取单天数据，最多 BATCH_SIZE 个 code（同一市场）。"""
        self._require_token()
        d_str = (fetch_date or date.today()).strftime('%Y-%m-%d')
        api_url = self._api_url(market)
        metrics = METRICS_BY_MARKET.get(market, CN_METRICS_LIST)
        all_data: list[dict[str, Any]] = []
        for i in range(0, len(codes), BATCH_SIZE):
            chunk = codes[i: i + BATCH_SIZE]
            payload: dict[str, Any] = {
                'token': self._token,
                'stockCodes': chunk,
                'date': d_str,
                'metricsList': metrics,
            }
            result = _post_with_retry(api_url, payload)
            if result.get('code') != 1:
                logger.warning('理杏仁批量请求失败 [%s]: %s', market, result.get('message'))
                continue
            all_data.extend(result.get('data', []))
        return all_data

    # ------------------------------------------------------------------
    # DataProvider 接口
    # ------------------------------------------------------------------
    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]:
        """历史回填：逐个指数，带日期区间"""
        try:
            raw = self._fetch_range(code, market, start_date)
        except DataFetchError:
            raise
        except Exception as e:
            raise DataFetchError(f'理杏仁历史抓取失败 {code}: {e}') from e

        if not raw:
            raise DataFetchError(f'理杏仁无历史数据 {code}')

        self._save_raw(raw)

        results = _parse_records(raw)
        if not results:
            raise DataFetchError(f'理杏仁无有效历史数据 {code}')
        return results

    def get_latest_batch(self, code_market_pairs: list[tuple[str, str]]) -> list[DailyMetrics]:
        """每日增量：按市场分组批量获取最新一条数据（≤100 个 code/请求）。

        Args:
            code_market_pairs: [(code, market), ...] 列表，支持混合市场
        """
        from collections import defaultdict
        by_market: dict[str, list[str]] = defaultdict(list)
        for code, market in code_market_pairs:
            by_market[market].append(code)

        all_raw: list[dict[str, Any]] = []
        for market, codes in by_market.items():
            try:
                raw = self._fetch_latest_batch(codes, market)
                all_raw.extend(raw)
            except DataFetchError:
                raise
            except Exception as e:
                raise DataFetchError(f'理杏仁批量抓取失败 [{market}]: {e}') from e

        if all_raw:
            self._save_raw(all_raw)

        return _parse_records(all_raw)

    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        results = self.get_latest_batch([(code, market)])
        if not results:
            raise DataFetchError(f'无法获取 {code} 最新数据')
        return results[0]

    # ------------------------------------------------------------------
    # 持久化原始数据
    # ------------------------------------------------------------------
    def _save_raw(self, records: list[dict[str, Any]]) -> None:
        """将原始 API 响应持久化到 lixinger_fundamentals 表"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.models.lixinger_fundamental import LixingerFundamental
        from app.core.config import settings

        engine = create_engine(settings.db_url_sync)
        try:
            with Session(engine) as session:
                for r in records:
                    d_str = r.get('date', '')
                    code = r.get('stockCode', '')
                    if not d_str or not code:
                        continue
                    try:
                        d = date.fromisoformat(d_str[:10])
                    except ValueError:
                        continue

                    raw_data = {k: v for k, v in r.items()
                                if k not in ('date', 'date2', 'stockCode')}

                    existing = session.query(LixingerFundamental).filter_by(
                        index_code=code, date=d
                    ).first()
                    if existing:
                        existing.data = raw_data
                    else:
                        session.add(LixingerFundamental(
                            index_code=code, date=d, data=raw_data
                        ))
                session.commit()
        except Exception as e:
            logger.warning('保存理杏仁原始数据失败: %s', e)
        finally:
            engine.dispose()
