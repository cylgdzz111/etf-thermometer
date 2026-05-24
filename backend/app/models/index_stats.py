from datetime import date
from sqlalchemy import String, Numeric, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class IndexStats(Base):
    __tablename__ = 'index_stats'

    index_code:    Mapped[str] = mapped_column(String(20), primary_key=True)

    # PE — 基于10年数据，用于列表温度
    pe_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    pe_min:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pe_max:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pe_avg:        Mapped[float | None] = mapped_column(Numeric(10, 4))

    # PB
    pb_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    pb_min:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb_max:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb_avg:        Mapped[float | None] = mapped_column(Numeric(10, 4))

    # PS
    ps_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ps_min:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    ps_max:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    ps_avg:        Mapped[float | None] = mapped_column(Numeric(10, 4))

    # DYR (股息率)
    dyr_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    dyr_min:        Mapped[float | None] = mapped_column(Numeric(10, 6))
    dyr_max:        Mapped[float | None] = mapped_column(Numeric(10, 6))
    dyr_avg:        Mapped[float | None] = mapped_column(Numeric(10, 6))

    # 分位数对应的交易日（daily_metrics 最新一行的 date）
    data_date:     Mapped[date | None] = mapped_column(Date)
    updated_at:    Mapped[DateTime | None] = mapped_column(DateTime)
