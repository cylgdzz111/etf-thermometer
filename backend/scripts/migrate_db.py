"""
纯 Python 数据库迁移脚本（不依赖 mysqldump / mysql 命令行）
将当前 .env 配置的源库完整迁移到新服务器 124.222.153.56

用法（在 backend/ 目录下执行）：
    .venv/bin/python -m scripts.migrate_db
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pymysql
from sqlalchemy import create_engine, inspect, text
from urllib.parse import quote_plus

from app.core.config import settings
from app.core.database import Base

# 注册所有 ORM Model，确保 metadata 收集完整
import app.models.index               # noqa
import app.models.daily_metrics       # noqa
import app.models.index_stats         # noqa
import app.models.lixinger_fundamental  # noqa

NEW_HOST = '124.222.153.56'
NEW_PORT = 3306
BATCH_SIZE = 2000   # 每批写入行数（daily_metrics 数据量大，适当调大）


# ── 连接工具 ──────────────────────────────────────────────────────

def _src_url() -> str:
    return settings.db_url_sync


def _dst_url(db: str = '') -> str:
    u = settings.DB_USER
    p = quote_plus(settings.DB_PASSWORD)
    suffix = f'/{db}' if db else ''
    return f'mysql+pymysql://{u}:{p}@{NEW_HOST}:{NEW_PORT}{suffix}'


# ── Step 1: 建库 ──────────────────────────────────────────────────

def create_database():
    print('Step 1  在目标服务器创建数据库...')
    conn = pymysql.connect(
        host=NEW_HOST, port=NEW_PORT,
        user=settings.DB_USER, password=settings.DB_PASSWORD,
        charset='utf8mb4',
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        print(f'  数据库 `{settings.DB_NAME}` 已就绪\n')
    finally:
        conn.close()


# ── Step 2: 建表（通过 ORM metadata） ─────────────────────────────

def create_schema(dst_engine):
    print('Step 2  在目标库创建表结构...')
    Base.metadata.create_all(dst_engine)

    # alembic_version 不在 ORM 里，单独建
    with dst_engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        conn.commit()
    print('  表结构已创建\n')


# ── Step 3: 按表逐批复制数据 ──────────────────────────────────────

def copy_table(table: str, src_engine, dst_engine):
    with src_engine.connect() as src:
        total = src.execute(text(f'SELECT COUNT(*) FROM `{table}`')).scalar()
        if total == 0:
            print(f'  {table}: 0 行，跳过')
            return

        # 获取列名
        cols = [col['name'] for col in inspect(src_engine).get_columns(table)]
        col_list  = ', '.join(f'`{c}`' for c in cols)
        placeholders = ', '.join(f':{c}' for c in cols)
        insert_sql = text(
            f'INSERT IGNORE INTO `{table}` ({col_list}) VALUES ({placeholders})'
        )

        offset = 0
        copied = 0
        with dst_engine.connect() as dst:
            while True:
                rows = src.execute(
                    text(f'SELECT {col_list} FROM `{table}` LIMIT {BATCH_SIZE} OFFSET {offset}')
                ).mappings().fetchall()
                if not rows:
                    break
                dst.execute(insert_sql, [dict(r) for r in rows])
                dst.commit()
                copied += len(rows)
                offset += BATCH_SIZE
                print(f'  {table}: {copied}/{total}', end='\r')

    print(f'  {table}: {total} 行 ✓          ')


def copy_all_tables(src_engine, dst_engine):
    print('Step 3  逐表复制数据...')
    # 按依赖顺序排列（alembic_version 最后，daily_metrics 数据量最大放后面）
    tables = [
        'alembic_version',
        'indices',
        'index_stats',
        'lixinger_fundamentals',
        'daily_metrics',
    ]
    for table in tables:
        copy_table(table, src_engine, dst_engine)
    print()


# ── Main ──────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print(f'源库  : {settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}')
    print(f'目标库: {settings.DB_USER}@{NEW_HOST}:{NEW_PORT}/{settings.DB_NAME}')
    print('=' * 60)
    print()

    src_engine = create_engine(_src_url(), echo=False)
    dst_engine = create_engine(_dst_url(settings.DB_NAME), echo=False)

    create_database()
    create_schema(dst_engine)
    copy_all_tables(src_engine, dst_engine)

    src_engine.dispose()
    dst_engine.dispose()

    print('=' * 60)
    print('迁移完成！')
    print()
    print('后续操作：')
    print(f'  1. 修改 backend/.env  DB_HOST={NEW_HOST}')
    print('  2. 重启 api 容器：docker compose restart api')
    print('=' * 60)


if __name__ == '__main__':
    main()
