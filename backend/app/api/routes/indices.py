from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...schemas.index import IndexRowSchema, IndexDetailSchema, IndexHistorySchema, ApiResponse

router = APIRouter()


@router.get('/indices', response_model=ApiResponse[list[IndexRowSchema]])
async def list_indices(
    market: str = Query('cn'),
    sector: str | None = Query(None),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # TODO Phase 3: 查询 indices + index_stats 表
    return ApiResponse(data=[])


@router.get('/indices/{code}', response_model=ApiResponse[IndexDetailSchema])
async def get_index(code: str, db: AsyncSession = Depends(get_db)):
    # TODO Phase 3
    return ApiResponse(data=None)


@router.get('/indices/{code}/history', response_model=ApiResponse[IndexHistorySchema])
async def get_index_history(
    code: str,
    range: str = Query('5y', pattern='^(1y|5y|all)$'),
    db: AsyncSession = Depends(get_db),
):
    # TODO Phase 3: 查询 daily_metrics 表
    return ApiResponse(data=IndexHistorySchema(price=[], pe=[], dates=[]))
