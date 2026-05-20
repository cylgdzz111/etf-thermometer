from sqlalchemy import BigInteger, String, Date, Numeric, DateTime, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class DailyMetrics(Base):
    __tablename__ = 'daily_metrics'
    __table_args__ = (
        UniqueConstraint('index_code', 'date', name='uq_code_date'),
        Index('idx_code_date', 'index_code', 'date'),
    )

    id:         Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(String(20), nullable=False)
    date:       Mapped[Date] = mapped_column(Date, nullable=False)
    close:      Mapped[float | None] = mapped_column(Numeric(12, 4))
    pe:         Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb:         Mapped[float | None] = mapped_column(Numeric(10, 4))
    ps:         Mapped[float | None] = mapped_column(Numeric(10, 4))
    dyr:        Mapped[float | None] = mapped_column(Numeric(10, 6))
    source:     Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
