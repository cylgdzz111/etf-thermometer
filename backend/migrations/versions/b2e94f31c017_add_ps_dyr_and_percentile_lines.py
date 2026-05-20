"""add ps dyr and percentile lines

Revision ID: b2e94f31c017
Revises: a3c81f20d9e2
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2e94f31c017'
down_revision = 'a3c81f20d9e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # daily_metrics: add ps, dyr
    op.add_column('daily_metrics', sa.Column('ps',  sa.Numeric(10, 4), nullable=True))
    op.add_column('daily_metrics', sa.Column('dyr', sa.Numeric(10, 6), nullable=True))

    # index_stats: add p30/p50/p80 for PE and PB
    op.add_column('index_stats', sa.Column('pe_p30', sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('pe_p50', sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('pe_p80', sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('pb_p30', sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('pb_p50', sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('pb_p80', sa.Numeric(10, 4), nullable=True))

    # index_stats: add full PS stats
    op.add_column('index_stats', sa.Column('ps_percentile', sa.Numeric(5, 2),  nullable=True))
    op.add_column('index_stats', sa.Column('ps_min',        sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('ps_max',        sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('ps_avg',        sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('ps_p30',        sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('ps_p50',        sa.Numeric(10, 4), nullable=True))
    op.add_column('index_stats', sa.Column('ps_p80',        sa.Numeric(10, 4), nullable=True))

    # index_stats: add full DYR stats
    op.add_column('index_stats', sa.Column('dyr_percentile', sa.Numeric(5, 2),  nullable=True))
    op.add_column('index_stats', sa.Column('dyr_min',        sa.Numeric(10, 6), nullable=True))
    op.add_column('index_stats', sa.Column('dyr_max',        sa.Numeric(10, 6), nullable=True))
    op.add_column('index_stats', sa.Column('dyr_avg',        sa.Numeric(10, 6), nullable=True))
    op.add_column('index_stats', sa.Column('dyr_p30',        sa.Numeric(10, 6), nullable=True))
    op.add_column('index_stats', sa.Column('dyr_p50',        sa.Numeric(10, 6), nullable=True))
    op.add_column('index_stats', sa.Column('dyr_p80',        sa.Numeric(10, 6), nullable=True))


def downgrade() -> None:
    for col in ('pe_p30', 'pe_p50', 'pe_p80', 'pb_p30', 'pb_p50', 'pb_p80',
                'ps_percentile', 'ps_min', 'ps_max', 'ps_avg', 'ps_p30', 'ps_p50', 'ps_p80',
                'dyr_percentile', 'dyr_min', 'dyr_max', 'dyr_avg', 'dyr_p30', 'dyr_p50', 'dyr_p80'):
        op.drop_column('index_stats', col)
    op.drop_column('daily_metrics', 'dyr')
    op.drop_column('daily_metrics', 'ps')
