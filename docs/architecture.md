# 系统架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                          VPS 服务器                           │
│                                                             │
│  ┌──────────┐    ┌────────────────┐    ┌─────────────────┐  │
│  │  Nginx   │───▶│   FastAPI      │───▶│    MySQL 8.0    │  │
│  │  :80/443 │    │  Python 3.11   │    │  etf_thermometer│  │
│  └──────────┘    └────────────────┘    └─────────────────┘  │
│       │                                        ▲            │
│  ┌────▼──────┐         ┌──────────────────────┐│            │
│  │ 前端静态   │         │   数据管道 / Scheduler ││            │
│  │ Vite 构建  │         │   每日 19:00 定时任务  │┘            │
│  └───────────┘         └──────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Docker Compose 服务划分**：
- `nginx`：反代 API + 托管前端静态文件
- `api`：FastAPI 应用
- `db`：MySQL 8.0
- `scheduler`：APScheduler 定时数据抓取任务

---

## 前端架构

**技术栈**：Vite + React 18 + TypeScript

**图表**：纯 SVG 自绘（参考 `design/charts.jsx`），不引入第三方图表库。

### 路由结构

```
/                     → Dashboard（市场估值概览）
/list                 → IndexList（指数估值列表）
/detail/:code         → Detail（指数详情）
/grid                 → GridStrategy（网格策略，Phase 5）
/correlation          → Correlation（相关性，Phase 5）
```

使用 React Router v6（无需 SSR）。

### 状态管理

- 全局：React Context（市场切换 `cn/hk/us`、主题）
- 本地：组件 useState
- 持久化：localStorage（收藏列表、用户偏好）
- 服务端状态：TanStack Query（接口缓存 + 自动刷新）

### 目录结构（前端）

```
frontend/
  src/
    api/          # API 请求封装（axios + tanstack query hooks）
    components/   # 通用组件（charts/, ui/）
    pages/        # 页面组件（Dashboard, List, Detail）
    store/        # Context providers
    types/        # TypeScript 类型定义
    utils/        # 工具函数（tempColor, tempLabel 等）
    App.tsx
    main.tsx
```

---

## 后端架构

**技术栈**：Python 3.11 + FastAPI + SQLAlchemy 2.0

### 目录结构（后端）

```
backend/
  app/
    api/          # 路由层（routes/）
    services/     # 业务逻辑层
    models/       # SQLAlchemy ORM 模型
    schemas/      # Pydantic 响应 Schema
    core/         # 配置、数据库连接
  scripts/
    fetch_daily.py   # 每日数据抓取入口
  providers/
    base.py          # DataProvider 抽象基类
    akshare.py       # A股/港股实现
    yfinance.py      # 美股实现
```

### API 端点规划

```
GET /api/markets                          # 可用市场列表
GET /api/market/{market}/overview         # Dashboard 数据
GET /api/indices?market=cn&sector=&q=     # 指数列表（带筛选）
GET /api/indices/{code}                   # 指数详情
GET /api/indices/{code}/history?range=5y  # 历史 PE/PB 数据
GET /api/sectors?market=cn               # 行业热力图数据
```

---

## 数据库设计

**数据库**：MySQL 8.0，库名 `etf_thermometer`

### 核心表

```sql
-- 指数主数据
CREATE TABLE indices (
  code        VARCHAR(20) PRIMARY KEY,
  market      ENUM('cn', 'hk', 'us') NOT NULL,
  name        VARCHAR(100) NOT NULL,
  sector      VARCHAR(50),
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 每日行情（带数据源字段，方便溯源）
CREATE TABLE daily_metrics (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  index_code  VARCHAR(20) NOT NULL,
  date        DATE NOT NULL,
  close       DECIMAL(12,4),
  pe          DECIMAL(10,4),
  pb          DECIMAL(10,4),
  source      VARCHAR(30) NOT NULL,       -- 'akshare'/'yfinance'/'manual'
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_code_date (index_code, date),
  INDEX idx_code_date (index_code, date)
);

-- 预计算分位数缓存（每晚 update，避免实时大查询）
CREATE TABLE index_stats (
  index_code    VARCHAR(20) PRIMARY KEY,
  pe_percentile DECIMAL(5,2),
  pb_percentile DECIMAL(5,2),
  pe_min        DECIMAL(10,4),
  pe_max        DECIMAL(10,4),
  pe_avg        DECIMAL(10,4),
  pb_min        DECIMAL(10,4),
  pb_max        DECIMAL(10,4),
  pb_avg        DECIMAL(10,4),
  temperature   DECIMAL(5,2),            -- (pe_percentile + pb_percentile) / 2
  updated_at    DATETIME
);
```

**分位数计算策略**：
- 基于近 10 年日数据（~2500 个交易日）
- 用 Python `numpy.percentile` 批量计算，每晚存入 `index_stats`
- API 直接读缓存，不在请求时实时计算

---

## 数据源抽象层

为支持后期扩展多数据渠道，所有数据抓取通过统一接口：

```python
class DataProvider(ABC):
    @abstractmethod
    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics: ...
    
    @abstractmethod
    def get_history(self, code: str, market: str, start_date: date) -> list[DailyMetrics]: ...

class CompositeProvider:
    """按市场路由，支持失败时 fallback 到备用源"""
    routing = {
        'cn': [AkshareProvider],
        'hk': [AkshareProvider],
        'us': [YFinanceProvider],
    }
```

新增数据渠道只需实现 `DataProvider` 接口，在 `routing` 中注册即可，不影响其他代码。

---

## 部署方案

**Docker Compose 服务**：

```yaml
services:
  nginx:    # 80/443，反代 /api → api:8000，其余托管 dist/
  api:      # FastAPI，内部 8000 端口
  db:       # MySQL 8.0，数据持久化挂载 volume
  scheduler:# 独立容器，共享 app/ 代码，运行定时任务
```

**CI/CD 流程**：
1. push 到 `main` 分支
2. GitHub Actions 构建前端 dist、构建 Docker 镜像
3. SSH 到 VPS，`docker-compose pull && docker-compose up -d`
