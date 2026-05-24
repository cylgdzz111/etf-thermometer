from datetime import date, datetime
from sqlalchemy import String, Enum, DateTime, Date, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class Index(Base):
    __tablename__ = 'indices'

    code        : Mapped[str]            = mapped_column(String(20), primary_key=True)
    market      : Mapped[str]            = mapped_column(Enum('cn', 'hk', 'us'), nullable=False)
    name        : Mapped[str]            = mapped_column(String(100), nullable=False)
    is_active   : Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False,
                                                         comment='是否参与数据抓取与前端展示')
    sector      : Mapped[str | None]     = mapped_column(String(50),  comment='手动维护的中文板块分类')

    # 来自理杏仁 /index 接口的元数据
    source      : Mapped[str | None]     = mapped_column(String(20),  comment='编制机构：csi/sse/hsi 等')
    currency    : Mapped[str | None]     = mapped_column(String(10),  comment='计价货币：CNY/HKD/USD')
    launch_date : Mapped[date | None]    = mapped_column(Date,        comment='指数发布日期')
    series      : Mapped[str | None]     = mapped_column(String(30),  comment='指数系列：size/style/sector/strategy')
    synced_at   : Mapped[datetime | None]= mapped_column(DateTime,    comment='最近一次从理杏仁同步的时间')

    created_at  : Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())
