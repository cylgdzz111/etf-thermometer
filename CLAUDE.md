# ETF 温度计 — Claude Code 项目入口

## 项目简介

ETF 温度计（ETF Thermometer）是一个实时展示 A 股、港股、美股 ETF/指数估值的 Web 应用。
核心功能：PE/PB 历史分位数计算（"温度"）、市场概览、指数列表、指数详情、行业热力图。

## 文档导航

| 文档 | 说明 |
|------|------|
| [docs/requirements.md](docs/requirements.md) | 产品需求文档（PRD），功能清单与优先级 |
| [docs/architecture.md](docs/architecture.md) | 系统架构设计，技术选型，数据流 |
| [docs/structure.md](docs/structure.md) | 项目目录结构与路由规划 |
| [docs/conventions.md](docs/conventions.md) | 前后端开发规范、Git 工作流 |
| [docs/data-sources.md](docs/data-sources.md) | 数据源说明、Provider 接口、字段映射 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vite + React 18 + TypeScript |
| 后端 | Python 3.11 + FastAPI |
| 数据库 | MySQL 8.0 |
| 数据抓取 | akshare（A股/港股）+ yfinance（美股） |
| 部署 | Docker Compose + Nginx，自有 VPS |

## 关键决策（已定，不再讨论）

- 前端纯 SPA，不用 Next.js SSR
- 图表用纯 SVG 自绘（参考 design/ 目录），不引入 ECharts/Recharts
- 数据源用 Provider 抽象层，支持后期替换/叠加多数据源
- PE/PB 历史分位数预计算后缓存，每晚更新一次，不实时计算
- 部署用 Docker Compose，统一管理前端/API/数据库/定时任务

## 开发阶段

- **Phase 1**：项目脚手架（Vite + FastAPI + MySQL + Docker Compose）
- **Phase 2**：数据管道（A股数据抓取 + 入库 + 分位数计算）
- **Phase 3**：三个核心视图接真实数据
- **Phase 4**：港股、美股数据接入

## 项目目录结构

```
etf-thermometer/
├── CLAUDE.md
├── .env.example               # DB_ROOT_PASSWORD / DB_PASSWORD
├── .gitignore
├── docker-compose.yml         # 生产编排
├── docker-compose.dev.yml     # 本地开发覆盖（热重载 + 暴露端口）
├── nginx/
│   └── default.conf           # 反代 /api → api:8000，其余托管静态文件
├── frontend/                  # Vite + React 18 + TypeScript SPA
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── styles/global.css  # CSS 变量 + 全局样式（--temp-0~6, --ink-1~4）
│   │   ├── types/index.ts     # 所有 TS 类型（Market, IndexRow, IndexDetail…）
│   │   ├── utils/temperature.ts # tempColor / tempLabel
│   │   ├── store/MarketContext.tsx
│   │   ├── api/
│   │   │   ├── client.ts      # axios 实例
│   │   │   ├── market.ts      # useMarketOverview hook
│   │   │   └── index.ts       # useIndexList / useIndexDetail / useIndexHistory
│   │   ├── components/
│   │   │   ├── charts/        # LineChart, Sparkline, DistributionChart,
│   │   │   │                  # PercentileChip, PBar — 纯 SVG，无外部依赖
│   │   │   └── ui/            # Nav, MarketSwitch
│   │   └── pages/
│   │       ├── Dashboard/     # 市场估值概览（Phase 3 接真实数据）
│   │       ├── IndexList/     # 指数估值列表（Phase 3）
│   │       └── Detail/        # 指数详情（Phase 3）
│   └── package.json
├── backend/                   # Python 3.11 + FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py            # FastAPI 入口，注册路由
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic Settings（DB_URL 等）
│   │   │   └── database.py    # AsyncEngine + get_db()
│   │   ├── models/            # SQLAlchemy ORM
│   │   │   ├── index.py       # indices 表
│   │   │   ├── daily_metrics.py
│   │   │   └── index_stats.py # 预计算分位数缓存
│   │   ├── schemas/           # Pydantic 响应模型
│   │   │   ├── index.py
│   │   │   └── market.py
│   │   └── api/routes/
│   │       ├── market.py      # GET /api/market/{market}/overview
│   │       └── indices.py     # GET /api/indices, /indices/{code}, /history
│   ├── providers/             # 数据源抽象层
│   │   ├── base.py            # DataProvider ABC + DailyMetrics dataclass
│   │   ├── composite.py       # 路由 + Fallback（ROUTING 字典）
│   │   ├── akshare_provider.py
│   │   └── yfinance_provider.py
│   ├── scripts/               # 定时任务脚本
│   │   └── fetch_daily.py     # Phase 2 实现
│   ├── migrations/            # Alembic
│   │   ├── env.py
│   │   └── versions/
│   └── tests/
└── docs/                      # 详细文档（见文档导航）
```

## 设计稿

原始设计稿在 `design/` 目录，包含 HTML 原型和 JSX 组件参考，开发时以此为视觉基准。

## 开发常用命令

```bash
# 前端开发
cd frontend && npm run dev        # http://localhost:5173

# 后端开发
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload     # http://localhost:8000

# 数据管道（手动触发）
cd backend && python -m scripts.fetch_daily

# Docker 全栈（生产模式）
cp .env.example .env && docker-compose up -d

# Docker 开发模式（热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 数据库 migration
cd backend && alembic revision --autogenerate -m "init"
alembic upgrade head
```
