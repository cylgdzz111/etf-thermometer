"""add lixinger_fundamentals table

Revision ID: a3c81f20d9e2
Revises: 5eb7f49de776
Create Date: 2026-05-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = 'a3c81f20d9e2'
down_revision: Union[str, None] = '5eb7f49de776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lixinger_fundamentals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('index_code', sa.String(length=16), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('data', mysql.JSON(), nullable=False,
                  comment='理杏仁 API 原始返回字段（除 date/stockCode）'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'),
                  onupdate=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('index_code', 'date', name='uq_lixinger_code_date'),
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_lixinger_fundamentals_index_code', 'lixinger_fundamentals', ['index_code'])
    op.create_index('ix_lixinger_fundamentals_date', 'lixinger_fundamentals', ['date'])


def downgrade() -> None:
    op.drop_index('ix_lixinger_fundamentals_date', 'lixinger_fundamentals')
    op.drop_index('ix_lixinger_fundamentals_index_code', 'lixinger_fundamentals')
    op.drop_table('lixinger_fundamentals')
