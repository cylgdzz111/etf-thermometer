from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class Index(Base):
    __tablename__ = 'indices'

    code:       Mapped[str] = mapped_column(String(20), primary_key=True)
    market:     Mapped[str] = mapped_column(Enum('cn', 'hk', 'us'), nullable=False)
    name:       Mapped[str] = mapped_column(String(100), nullable=False)
    sector:     Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
