from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...schemas.market import MarketOverviewSchema
from ...schemas.index import ApiResponse

router = APIRouter()


@router.get('/market/{market}/overview', response_model=ApiResponse[MarketOverviewSchema])
async def get_market_overview(market: str, db: AsyncSession = Depends(get_db)):
    # TODO Phase 3: 从数据库聚合真实数据
    return ApiResponse(data=MarketOverviewSchema(
        market=market,
        temperature=None,
        updated_at=None,
        headlines=[],
        sectors=[],
        series={},
    ))
