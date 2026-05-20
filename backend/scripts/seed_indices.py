"""
初始化 A 股指数主数据（20 个，来自设计稿）
用法：python -m scripts.seed_indices
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.index import Index

# A 股指数列表
# (code, name, sector, akshare_name)
# akshare_name: index_value_hist_funddb 接口使用的中文名称，None 表示暂无 PE/PB 数据
CN_INDICES = [
    # 宽基
    ('000300', '沪深300',    '宽基', '沪深300'),
    ('000905', '中证500',    '宽基', '中证500'),
    ('000852', '中证1000',   '宽基', '中证1000'),
    ('399006', '创业板指',   '宽基', '创业板指'),
    ('000016', '上证50',     '宽基', '上证50'),
    ('000688', '科创50',     '宽基', '科创50'),
    # 消费 / 医药 / 金融
    ('399987', '中证酒',     '消费', '中证酒'),
    ('000978', '医药100',    '医药', '医药100'),
    ('399986', '中证银行',   '金融', '中证银行'),
    ('399975', '证券公司',   '金融', '证券公司'),
    # 新能源
    ('399976', '新能源车',   '新能源', '新能源车'),
    ('931151', '光伏产业',   '新能源', '光伏产业'),
    # 军工 / 科技
    ('931594', '卫星产业',   '军工', None),   # akshare 暂无
    ('931066', '军工龙头',   '军工', None),
    ('931521', '高端装备50', '军工', None),
    ('931866', '中证机床',   '装备', None),
    ('h30590', '机器人',     '机器人', None),
    ('930875', '空天军工',   '军工', None),
    ('399973', '中证国防',   '军工', '中证国防'),
    ('399967', '中证军工',   '军工', '中证军工'),
]


async def seed():
    async with AsyncSessionLocal() as session:
        inserted, skipped = 0, 0
        for code, name, sector, akshare_name in CN_INDICES:
            existing = await session.get(Index, code)
            if existing:
                skipped += 1
                continue
            session.add(Index(
                code=code,
                market='cn',
                name=name,
                sector=sector,
                akshare_name=akshare_name,
            ))
            inserted += 1
        await session.commit()
        print(f'Done: {inserted} inserted, {skipped} skipped')


async def main():
    await seed()
    # 确保连接池在 event loop 关闭前释放
    from app.core.database import engine
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
