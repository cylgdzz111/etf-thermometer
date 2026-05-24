"""
生成小红书图片：每日汇总 + 指数详情
用法：
  python -m scripts.generate_images --type summary
  python -m scripts.generate_images --type detail --code 000300
  python -m scripts.generate_images --all
"""
import asyncio
import argparse
import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.index import Index
from app.models.daily_metrics import DailyMetrics
from app.models.index_stats import IndexStats

TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'
OUTPUT_DIR    = Path(__file__).parent.parent.parent / 'output'

# 每日汇总展示的指数分组（按市场）
SUMMARY_GROUPS = {
    'cn': {
        'label': 'A股',
        'codes': ['000300', '000016', '000905', '000852', '399006', '000688', '000922'],
    },
    'hk': {
        'label': '港股',
        'codes': ['HSI', 'HSTECH'],
    },
}

# 支持详情图的指数
DETAIL_CODES = ['000300', '000016', '000905', '000852']


def _sig(pct: float | None) -> str:
    if pct is None:
        return 'y'
    if pct < 30:
        return 'g'
    if pct < 70:
        return 'y'
    return 'r'


def _date_ctx() -> dict:
    today = date.today()
    cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    en = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    wd = today.weekday()
    return {
        'date_mmdd':    today.strftime('%Y.%m.%d'),
        'date_weekday': f'{en[wd]} · {cn[wd]}',
    }


async def _query_summary(session) -> list[dict]:
    """返回按市场分组的数据: [{label, indices: [...]}, ...]"""
    all_codes = [c for g in SUMMARY_GROUPS.values() for c in g['codes']]

    rows = (await session.execute(
        select(Index, IndexStats)
        .join(IndexStats, Index.code == IndexStats.index_code)
        .where(Index.code.in_(all_codes), Index.is_active == True)  # noqa: E712
    )).all()

    stats_map = {idx.code: (idx, s) for idx, s in rows}
    groups = []
    for group_info in SUMMARY_GROUPS.values():
        items = []
        for code in group_info['codes']:
            if code not in stats_map:
                continue
            idx, s = stats_map[code]
            items.append({
                'name': idx.name,
                'code': code,
                'pe':  round(s.pe_percentile)  if s.pe_percentile  is not None else None,
                'ps':  round(s.ps_percentile)  if s.ps_percentile  is not None else None,
                'pb':  round(s.pb_percentile)  if s.pb_percentile  is not None else None,
                'div': round(s.dyr_percentile) if s.dyr_percentile is not None else None,
            })
        if items:
            groups.append({'label': group_info['label'], 'indices': items})
    return groups


async def _query_detail(session, code: str) -> dict:
    idx = (await session.execute(
        select(Index).where(Index.code == code)
    )).scalar_one_or_none()

    s = (await session.execute(
        select(IndexStats).where(IndexStats.index_code == code)
    )).scalar_one_or_none()

    cutoff = date.today() - timedelta(days=365 * 10)
    rows = (await session.execute(
        select(DailyMetrics.date, DailyMetrics.close,
               DailyMetrics.pe, DailyMetrics.pb, DailyMetrics.ps)
        .where(DailyMetrics.index_code == code, DailyMetrics.date >= cutoff)
        .order_by(DailyMetrics.date)
    )).all()

    dates = [r.date.strftime('%Y-%m-%d') for r in rows]
    series = {
        'price': [float(r.close) if r.close is not None else None for r in rows],
        'pe':    [float(r.pe)    if r.pe    is not None else None for r in rows],
        'pb':    [float(r.pb)    if r.pb    is not None else None for r in rows],
        'ps':    [float(r.ps)    if r.ps    is not None else None for r in rows],
    }

    def _pctiles(vals: list) -> dict:
        arr = np.array([v for v in vals if v is not None], dtype=float)
        if len(arr) < 20:
            return {'p30': None, 'p50': None, 'p80': None}
        return {
            'p30': round(float(np.percentile(arr, 30)), 4),
            'p50': round(float(np.percentile(arr, 50)), 4),
            'p80': round(float(np.percentile(arr, 80)), 4),
        }

    latest = rows[-1] if rows else None

    def _cur(val, pct_field):
        pct = getattr(s, pct_field, None) if s else None
        return {
            'val': round(float(val), 4) if val is not None else None,
            'pct': round(pct) if pct is not None else None,
            'sig': _sig(pct),
        }

    return {
        'index_name': idx.name if idx else code,
        'index_code': code,
        'close_fmt':  f'{float(latest.close):,.2f}' if latest and latest.close is not None else '—',
        'dates':   dates,
        'series':  series,
        'pctiles': {
            'pe': _pctiles(series['pe']),
            'pb': _pctiles(series['pb']),
            'ps': _pctiles(series['ps']),
        },
        'current': {
            'pe': _cur(latest.pe if latest else None, 'pe_percentile'),
            'pb': _cur(latest.pb if latest else None, 'pb_percentile'),
            'ps': _cur(latest.ps if latest else None, 'ps_percentile'),
        },
    }


async def _screenshot(html: str, output_path: Path, width: int = 1080, height: int = 1440):
    with tempfile.NamedTemporaryFile(
        suffix='.html', delete=False, mode='w', encoding='utf-8'
    ) as f:
        f.write(html)
        tmp = f.name
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=2)
            await page.goto(f'file://{tmp}')
            await page.wait_for_load_state('networkidle')
            canvas = page.locator('#canvas')
            await canvas.screenshot(path=str(output_path))
            await browser.close()
    finally:
        os.unlink(tmp)
    print(f'  saved → {output_path}')


def _render(template_name: str, ctx: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    return env.get_template(template_name).render(**ctx)


async def generate_summary():
    async with AsyncSessionLocal() as session:
        groups = await _query_summary(session)

    html = _render('daily_summary.html', {
        **_date_ctx(),
        'groups_json': json.dumps(groups, ensure_ascii=False),
    })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    await _screenshot(html, OUTPUT_DIR / f'summary_{date.today():%Y%m%d}.png', width=380, height=820)


async def generate_detail(code: str):
    async with AsyncSessionLocal() as session:
        data = await _query_detail(session, code)

    html = _render('index_detail.html', {
        **_date_ctx(),
        'index_name': data['index_name'],
        'index_code': data['index_code'],
        'close_fmt':  data['close_fmt'],
        'series_json':  json.dumps(data['series'],  ensure_ascii=False),
        'dates_json':   json.dumps(data['dates'],   ensure_ascii=False),
        'pctiles_json': json.dumps(data['pctiles'], ensure_ascii=False),
        'current_json': json.dumps(data['current'], ensure_ascii=False),
    })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    await _screenshot(html, OUTPUT_DIR / f'detail_{code}_{date.today():%Y%m%d}.png')


async def main():
    parser = argparse.ArgumentParser(description='生成小红书图片')
    parser.add_argument('--type', choices=['summary', 'detail'])
    parser.add_argument('--code', default='000300', help='指数代码，--type detail 时使用')
    parser.add_argument('--all',  action='store_true', help='生成全部图片')
    args = parser.parse_args()

    if args.all:
        print('生成每日汇总...')
        await generate_summary()
        for code in DETAIL_CODES:
            print(f'生成详情 {code}...')
            await generate_detail(code)
    elif args.type == 'summary':
        await generate_summary()
    elif args.type == 'detail':
        await generate_detail(args.code)
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
