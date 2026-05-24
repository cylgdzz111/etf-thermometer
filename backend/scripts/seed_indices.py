"""
手动初始化指定指数并激活（is_active=True）
适合在 sync_indices 同步完元数据后，批量激活已知想跟踪的指数。

用法：python -m scripts.seed_indices
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal, engine
from app.models.index import Index

# 需要激活的指数：(code, market, name, sector)
# 运行 sync_indices 后这些指数已存在于 indices 表，这里只做激活 + 补充 sector
ACTIVE_INDICES = [
    # ── A 股宽基 ──────────────────────────────────────────────────
    ('000300', 'cn', '沪深300',    '宽基'),
    ('000905', 'cn', '中证500',    '宽基'),
    ('000852', 'cn', '中证1000',   '宽基'),
    ('399006', 'cn', '创业板指',   '宽基'),
    ('000016', 'cn', '上证50',     '宽基'),
    ('000688', 'cn', '科创50',     '宽基'),
    # ── A 股行业 ──────────────────────────────────────────────────
    ('399987', 'cn', '中证酒',     '消费'),
    ('000978', 'cn', '医药100',    '医药'),
    ('399986', 'cn', '中证银行',   '金融'),
    ('399975', 'cn', '证券公司',   '金融'),
    ('399976', 'cn', '新能源车',   '新能源'),
    ('931151', 'cn', '光伏产业',   '新能源'),
    ('931594', 'cn', '卫星产业',   '军工'),
    ('931066', 'cn', '军工龙头',   '军工'),
    ('931521', 'cn', '高端装备50', '军工'),
    ('931866', 'cn', '中证机床',   '装备'),
    ('h30590', 'cn', '机器人',     '机器人'),
    ('930875', 'cn', '空天军工',   '军工'),
    ('399973', 'cn', '中证国防',   '军工'),
    ('399967', 'cn', '中证军工',   '军工'),
    # ── 港股 ──────────────────────────────────────────────────────
    ('HSI',    'hk', '恒生指数',   '宽基'),
    ('HSTECH', 'hk', '恒生科技',   '科技'),
]


async def seed():
    async with AsyncSessionLocal() as session:
        activated = inserted = skipped = 0

        for code, market, name, sector in ACTIVE_INDICES:
            existing = await session.get(Index, code)
            if existing:
                # 已存在：激活并补充 sector（不覆盖其他字段）
                existing.is_active = True
                if not existing.sector:
                    existing.sector = sector
                activated += 1
            else:
                # 不存在时直接插入（兼容未运行 sync_indices 的情况）
                session.add(Index(
                    code=code, market=market,
                    name=name, sector=sector,
                    is_active=True,
                ))
                inserted += 1

        await session.commit()
        print(f'Done: activated={activated}, inserted={inserted}, skipped={skipped}')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(seed())
