# 开发规范

## Git 工作流

### 分支策略

```
main          # 生产分支，只接受 PR 合并，自动触发部署
dev           # 开发集成分支
feat/*        # 功能开发分支，从 dev 切出
fix/*         # Bug 修复分支
```

### Commit 规范

格式：`<type>(<scope>): <subject>`

| type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `data` | 数据相关（抓取、schema 变更） |
| `refactor` | 重构，不改变功能 |
| `style` | 样式调整 |
| `docs` | 文档 |
| `chore` | 构建、依赖、配置 |

示例：
```
feat(list): add PE percentile filter chips
fix(provider): handle akshare timeout for HK indices
data(schema): add source field to daily_metrics
```

---

## 前端规范

### TypeScript

- 所有新文件使用 TypeScript（`.tsx` / `.ts`）
- 不用 `any`，未知类型用 `unknown`
- API 响应类型统一在 `src/types/index.ts` 定义
- 组件 Props 用 `interface`，不用 `type`

### React 组件

- 函数组件 + Hooks，不用 class 组件
- 组件文件名 PascalCase：`HeadlineCard.tsx`
- 页面级组件放 `pages/`，可复用组件放 `components/`
- 每个组件只做一件事，超过 200 行考虑拆分

### 图表组件

- 所有图表继承 `design/charts.jsx` 的 SVG 实现思路
- 图表组件接收纯数据（数组/对象），不在图表内部发请求
- 宽高通过 props 传入，内部用 `viewBox` 保证响应式

### 样式

- 使用 CSS Modules（`.module.css`），与设计稿 `design/styles.css` 保持变量名一致
- CSS 变量沿用设计稿中的 `--temp-0` ~ `--temp-6`、`--ink-1` ~ `--ink-4` 等
- 不引入 Tailwind 或 CSS-in-JS，保持轻量

### 数据请求

- 统一用 TanStack Query（react-query）管理服务端状态
- API 函数封装在 `src/api/` 对应文件，组件内只调用 hook
- 错误边界：列表/图表加载失败展示空状态，不崩溃整页

---

## 后端规范

### Python 风格

- Python 3.11+，遵循 PEP 8
- 类型注解必须写（函数参数 + 返回值）
- 用 `Pydantic v2` 做数据校验和序列化

### FastAPI 接口

- 路由函数只做参数解析和响应组装，业务逻辑放 `services/`
- 统一响应格式：
  ```json
  { "data": ..., "updated_at": "2026-05-20T19:00:00" }
  ```
- 错误响应用 `HTTPException`，不自定义错误码

### 数据库操作

- 使用 SQLAlchemy 2.0 异步模式（`AsyncSession`）
- 不在 ORM 层写复杂逻辑，复杂查询用原生 SQL
- 数据库 migration 用 Alembic 管理，不手动改表结构

### 数据源 Provider

- 每个 Provider 只负责"获取原始数据"，不做业务计算
- Provider 内捕获所有外部异常，转为内部 `DataFetchError`
- `CompositeProvider` 负责 fallback 逻辑，调用方无需感知

### 分位数计算

- 基准：取该指数历史 **全部** 日数据（最少要有 1 年，否则标记为数据不足）
- 公式：`percentile = (当前PE < 历史PE的天数) / 总天数 * 100`
- 每日收盘后（22:00）批量重算并写入 `index_stats`

---

## 环境变量

所有敏感配置通过环境变量注入，不硬编码在代码中。

```bash
# backend/.env（不提交 Git）
DB_URL=mysql+aiomysql://user:pass@db:3306/etf_thermometer
API_SECRET=...
TUSHARE_TOKEN=...       # 预留，暂时不用
```

`.env.example` 提交 Git，列出所有变量名（不含值）。

---

## 测试规范

- Provider 层必须有单元测试（mock 外部 API）
- API 层有集成测试（用测试数据库）
- 前端图表组件有 snapshot 测试（防样式回归）
- 不要求 100% 覆盖率，核心数据链路（抓取→存储→计算→API）需要测试
