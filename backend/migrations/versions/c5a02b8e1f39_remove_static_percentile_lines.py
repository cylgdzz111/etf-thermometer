"""remove static percentile lines from index_stats

Revision ID: c5a02b8e1f39
Revises: b2e94f31c017
Create Date: 2026-05-20

分位线改为按请求时间区间动态计算后随 history 接口返回，不再预存储。
"""
from alembic import op

revision = 'c5a02b8e1f39'
down_revision = 'b2e94f31c017'
branch_labels = None
depends_on = None

_COLS = [
    'pe_p30', 'pe_p50', 'pe_p80',
    'pb_p30', 'pb_p50', 'pb_p80',
    'ps_p30', 'ps_p50', 'ps_p80',
    'dyr_p30', 'dyr_p50', 'dyr_p80',
]


def upgrade() -> None:
    for col in _COLS:
        op.drop_column('index_stats', col)


def downgrade() -> None:
    import sqlalchemy as sa
    for col in _COLS:
        prec = (10, 6) if col.startswith('dyr') else (10, 4)
        op.add_column('index_stats', sa.Column(col, sa.Numeric(*prec), nullable=True))
