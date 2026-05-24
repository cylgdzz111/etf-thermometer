"""
请求日志中间件

每个 HTTP 请求完成后记录一行：
  文本格式：2026-05-21 18:00:01 INFO     [api.access] GET /api/indices/000905 → 200 23ms
  JSON 格式：{"time":...,"level":"INFO","method":"GET","path":"/api/indices/000905","status":200,"duration_ms":23}

4xx 使用 WARNING 级别，5xx 使用 ERROR 级别，便于日志平台过滤告警。
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger('api.access')


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:8]
        request.state.request_id = request_id   # 路由内可通过 request.state.request_id 读取
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # 未被 exception_handler 捕获的裸异常（极少见）
            duration_ms = round((time.perf_counter() - start) * 1000)
            logger.error(
                '%s %s → 500 %dms [%s]',
                request.method, request.url.path, duration_ms, request_id,
                extra=_extra(request, 500, duration_ms, request_id),
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000)
        status = response.status_code

        if status >= 500:
            level = logging.ERROR
        elif status >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        logger.log(
            level,
            '%s %s → %d %dms [%s]',
            request.method, request.url.path, status, duration_ms, request_id,
            extra=_extra(request, status, duration_ms, request_id),
        )
        return response


def _extra(request: Request, status: int, duration_ms: int, request_id: str) -> dict:
    return {
        'request_id': request_id,
        'method':     request.method,
        'path':       request.url.path,
        'status':     status,
        'duration_ms': duration_ms,
        'client':     request.client.host if request.client else '-',
    }
