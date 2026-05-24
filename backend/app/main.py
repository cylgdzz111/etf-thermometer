import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import market, indices
from .core.config import settings
from .core.logging_config import setup_logging
from .middleware.logging import RequestLoggingMiddleware

# 应用启动时最先初始化日志，确保后续所有模块的日志都走统一配置
setup_logging(
    level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    json_format=settings.LOG_JSON,
)

logger = logging.getLogger('api')

app = FastAPI(title='ETF Thermometer API', version='0.1.0')

# ── 中间件（注册顺序 = 洋葱外层 → 内层，即后注册的先执行）────────
app.add_middleware(RequestLoggingMiddleware)   # 最外层：计时 + 记录访问日志
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_methods=['GET'],
    allow_headers=['*'],
)

# ── 全局异常处理器 ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, 'request_id', '-')
    logger.error(
        '未处理异常 %s %s [%s]: %s',
        request.method, request.url.path, request_id, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error', 'request_id': request_id},
    )

# ── 路由 ──────────────────────────────────────────────────────────
app.include_router(market.router, prefix='/api')
app.include_router(indices.router, prefix='/api')


@app.get('/api/health')
async def health():
    return {'status': 'ok'}
