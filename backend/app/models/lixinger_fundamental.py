from sqlalchemy import Column, String, Date, JSON, Integer, UniqueConstraint, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class LixingerFundamental(Base):
    """理杏仁原始基本面数据，保留 API 所有字段供后续分析"""

    __tablename__ = 'lixinger_fundamentals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_code = Column(String(16), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    data = Column(JSON, nullable=False, comment='理杏仁 API 原始返回字段（除 date/stockCode）')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('index_code', 'date', name='uq_lixinger_code_date'),
        {'mysql_charset': 'utf8mb4'},
    )
