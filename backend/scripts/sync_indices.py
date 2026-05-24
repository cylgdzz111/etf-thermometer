"""
从理杏仁同步全量指数元数据到 indices 表

行为：
  - 新指数：插入，is_active=False（默认不激活）
  - 已有指数：仅更新 name/source/currency/launch_date/series/synced_at，
              不覆盖 is_active / sector（用户手动维护的字段）

用法（在 backend/ 目录下执行）：
  .venv/bin/python -m scripts.sync_indices          # 同步 cn + hk
  .venv/bin/python -m scripts.sync_indices --market cn
  .venv/bin/python -m scripts.sync_indices --market hk
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, date

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.models.index import Index

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('sync_indices')

LIXINGER_INDEX_APIS = {
    'cn': 'https://open.lixinger.com/api/cn/index',
    'hk': 'https://open.lixinger.com/api/hk/index',
}
HEADERS = {'Accept-Encoding': 'gzip', 'Content-Type': 'application/json'}


def _fetch_index_list(market: str, token: str) -> list[dict]:
    """调用理杏仁指数列表接口，返回原始数据列表。"""
    url = LIXINGER_INDEX_APIS[market]
    resp = requests.post(url, json={'token': token}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 1:
        raise RuntimeError(f'理杏仁接口错误 [{market}]: {data.get("message")}')
    return data.get('data', [])


def _parse_launch_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw[:10]).date()
    except ValueError:
        return None


async def _sync_market(market: str, token: str):
    logger.info('开始同步 %s 市场指数...', market)
    items = _fetch_index_list(market, token)
    logger.info('共获取 %d 条指数', len(items))

    now = datetime.now()
    inserted = updated = 0

    async with AsyncSessionLocal() as session:
        for item in items:
            code = item.get('stockCode', '').strip()
            name = item.get('name', '').strip()
            if not code or not name:
                continue

            existing = await session.get(Index, code)
            if existing:
                # 只更新来自 API 的字段，不碰 is_active / sector
                existing.name        = name
                existing.source      = item.get('source')
                existing.currency    = item.get('currency')
                existing.launch_date = _parse_launch_date(item.get('launchDate'))
                existing.series      = item.get('series')
                existing.synced_at   = now
                updated += 1
            else:
                session.add(Index(
                    code        = code,
                    market      = market,
                    name        = name,
                    is_active   = False,
                    source      = item.get('source'),
                    currency    = item.get('currency'),
                    launch_date = _parse_launch_date(item.get('launchDate')),
                    series      = item.get('series'),
                    synced_at   = now,
                ))
                inserted += 1

        await session.commit()

    logger.info('%s 市场同步完成：新增 %d 条，更新 %d 条', market, inserted, updated)


async def main_async(markets: list[str]):
    if not settings.LIXINGER_TOKEN:
        logger.error('LIXINGER_TOKEN 未配置，请在 .env 中填写')
        sys.exit(1)

    for market in markets:
        await _sync_market(market, settings.LIXINGER_TOKEN)

    await engine.dispose()
    logger.info('全部同步完成')
    logger.info('')
    logger.info('下一步：使用以下 SQL 激活需要跟踪的指数：')
    logger.info("  UPDATE indices SET is_active=1 WHERE code IN ('000300','000905',...);")


def main():
    parser = argparse.ArgumentParser(description='从理杏仁同步指数元数据')
    parser.add_argument('--market', choices=['cn', 'hk'], help='只同步指定市场；默认同步全部')
    args = parser.parse_args()

    markets = [args.market] if args.market else ['cn', 'hk']
    asyncio.run(main_async(markets))


if __name__ == '__main__':
    main()
