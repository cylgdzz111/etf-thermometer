from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class IndexStats(Base):
    __tablename__ = 'index_stats'

    index_code:    Mapped[str] = mapped_column(String(20), primary_key=True)
    pe_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    pb_percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    pe_min:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pe_max:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pe_avg:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb_min:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb_max:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    pb_avg:        Mapped[float | None] = mapped_column(Numeric(10, 4))
    temperature:   Mapped[float | None] = mapped_column(Numeric(5, 2))
    updated_at:    Mapped[DateTime | None] = mapped_column(DateTime)
