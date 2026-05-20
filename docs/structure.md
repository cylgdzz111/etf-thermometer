# 项目目录结构

## 顶层结构

```
etf-thermometer/
  ├── frontend/          # Vite + React + TypeScript 前端
  ├── backend/           # Python + FastAPI 后端 + 数据管道
  ├── design/            # 原始设计稿（只读参考，不进入生产构建）
  ├── docs/              # 项目文档
  ├── docker-compose.yml # 全栈编排
  ├── docker-compose.dev.yml  # 本地开发覆盖配置
  ├── .github/
  │   └── workflows/
  │       └── deploy.yml # CI/CD
  └── CLAUDE.md          # Claude Code 入口文档
```

---

## 前端目录

```
frontend/
  ├── public/
  ├── src/
  │   ├── api/                  # 接口请求层
  │   │   ├── client.ts         # axios 实例配置
  │   │   ├── market.ts         # 市场概览接口
  │   │   ├── index.ts          # 指数列表/详情接口
  │   │   └── sector.ts         # 行业数据接口
  │   ├── components/
  │   │   ├── charts/           # 纯 SVG 图表组件
  │   │   │   ├── LineChart.tsx
  │   │   │   ├── Sparkline.tsx
  │   │   │   ├── DistributionChart.tsx
  │   │   │   ├── ThermoBar.tsx
  │   │   │   └── PercentileChip.tsx
  │   │   └── ui/               # 通用 UI 组件
  │   │       ├── Nav.tsx
  │   │       ├── MarketSwitch.tsx
  │   │       └── ...
  │   ├── pages/
  │   │   ├── Dashboard/        # 市场估值概览
  │   │   │   ├── index.tsx
  │   │   │   ├── HeadlineCard.tsx
  │   │   │   └── SectorCell.tsx
  │   │   ├── IndexList/        # 指数估值列表
  │   │   │   └── index.tsx
  │   │   └── Detail/           # 指数详情
  │   │       └── index.tsx
  │   ├── store/
  │   │   └── MarketContext.tsx  # 全局市场切换 Context
  │   ├── types/
  │   │   └── index.ts          # 所有 TypeScript 类型定义
  │   ├── utils/
  │   │   └── temperature.ts    # tempColor / tempLabel 等工具函数
  │   ├── App.tsx
  │   └── main.tsx
  ├── index.html
  ├── vite.config.ts
  ├── tsconfig.json
  └── package.json
```

---

## 后端目录

```
backend/
  ├── app/
  │   ├── api/
  │   │   └── routes/
  │   │       ├── market.py     # GET /api/market/{market}/overview
  │   │       ├── indices.py    # GET /api/indices, /api/indices/{code}
  │   │       └── sectors.py    # GET /api/sectors
  │   ├── services/
  │   │   ├── market_service.py
  │   │   ├── index_service.py
  │   │   └── stats_service.py  # 分位数计算逻辑
  │   ├── models/               # SQLAlchemy ORM
  │   │   ├── index.py
  │   │   ├── daily_metrics.py
  │   │   └── index_stats.py
  │   ├── schemas/              # Pydantic 响应模型
  │   │   ├── market.py
  │   │   └── index.py
  │   ├── core/
  │   │   ├── config.py         # 环境变量配置
  │   │   └── database.py       # SQLAlchemy engine / session
  │   └── main.py               # FastAPI app 入口
  ├── providers/                # 数据源抽象层
  │   ├── base.py               # DataProvider 抽象基类
  │   ├── composite.py          # CompositeProvider（路由 + fallback）
  │   ├── akshare_provider.py   # A股/港股实现
  │   └── yfinance_provider.py  # 美股实现
  ├── scripts/
  │   ├── fetch_daily.py        # 每日行情抓取入口
  │   ├── calc_stats.py         # 分位数批量计算
  │   └── seed_indices.py       # 初始化指数主数据
  ├── tests/
  │   ├── test_providers.py
  │   └── test_api.py
  ├── requirements.txt
  ├── Dockerfile
  └── .env.example
```

---

## Docker 配置

```
docker-compose.yml          # 生产配置（镜像名、restart: always、volume）
docker-compose.dev.yml      # 开发覆盖（挂载本地代码、热重载）
nginx/
  └── default.conf          # nginx 反代配置
```

---

## 前端路由

| URL | 页面组件 | 说明 |
|-----|---------|------|
| `/` | `Dashboard` | 市场估值概览，默认 A股 |
| `/list` | `IndexList` | 指数估值列表 |
| `/detail/:code` | `Detail` | 指数详情，`:code` 为指数代码 |
| `/grid` | `GridStrategy` | 网格策略（Phase 5） |
| `/correlation` | `Correlation` | 相关性分析（Phase 5） |

---

## 后端 API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/markets` | 可用市场列表 |
| GET | `/api/market/{market}/overview` | Dashboard 聚合数据 |
| GET | `/api/indices` | 指数列表，支持 `?market=cn&sector=&q=` |
| GET | `/api/indices/{code}` | 指数基本信息 + 当前估值 |
| GET | `/api/indices/{code}/history` | 历史 PE/PB，支持 `?range=1y|5y|all` |
| GET | `/api/sectors` | 行业热力图数据，支持 `?market=cn` |
