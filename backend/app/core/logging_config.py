"""
日志初始化模块

支持两种格式：
  - 文本格式（默认，本地开发友好）
  - JSON 格式（生产推荐，可直接被 Loki / ELK 解析）

支持两种输出：
  - stdout（始终开启）
  - 按天轮转日志文件（LOG_DIR 不为空时开启，保留 30 天）
"""
import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path


class _JsonFormatter(logging.Formatter):
    """将 LogRecord 序列化为单行 JSON。"""

    # 需要从 extra 透传到 JSON 的字段
    EXTRA_KEYS = ('request_id', 'method', 'path', 'status', 'duration_ms', 'client')

    def format(self, record: logging.LogRecord) -> str:
        log: dict = {
            'time':    datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            'level':   record.levelname,
            'logger':  record.name,
            'message': record.getMessage(),
        }
        for key in self.EXTRA_KEYS:
            val = record.__dict__.get(key)
            if val is not None:
                log[key] = val
        if record.exc_info:
            log['exc'] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)


_TEXT_FMT = logging.Formatter(
    fmt='%(asctime)s %(levelname)-8s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def setup_logging(
    level: str = 'INFO',
    log_dir: str = '',
    json_format: bool = False,
) -> None:
    """
    全局日志配置，应在应用启动最早期调用一次。

    Args:
        level:       日志级别字符串，如 'DEBUG' / 'INFO' / 'WARNING'
        log_dir:     日志文件目录；空字符串表示不写文件
        json_format: True → JSON 格式；False → 人读文本格式
    """
    formatter = _JsonFormatter() if json_format else _TEXT_FMT

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()

    # ── stdout ────────────────────────────────────────────────────
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    # ── 按天轮转文件 ──────────────────────────────────────────────
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.TimedRotatingFileHandler(
            filename=log_path / 'api.log',
            when='midnight',
            backupCount=30,
            encoding='utf-8',
        )
        fh.setFormatter(formatter)
        root.addHandler(fh)

    # ── 压低三方库噪音 ────────────────────────────────────────────
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)   # 由中间件接管
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
