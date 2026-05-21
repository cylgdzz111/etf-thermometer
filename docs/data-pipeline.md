# 数据管道使用文档

数据管道负责从各数据源抓取历史行情和估值指标，写入数据库，并计算 PE/PB/PS/股息率的历史分位数。

---

## 数据流向

```
理杏仁 API  ──┐
              ├──► daily_metrics 表 ──► calc_stats ──► index_stats 表
akshare API ──┘                                        （温度 / 分位数）
```

| 表 | 内容 |
|----|------|
| `daily_metrics` | 每日行情：收盘价、PE、PB、PS、股息率 |
| `index_stats` | 预计算结果：10年分位数、min/max/avg、综合温度 |

---

## 前提条件

### 配置 `LIXINGER_TOKEN`

理杏仁 PE/PB/PS/股息率数据需要 Token，在 `backend/.env` 中填入：

```
LIXINGER_TOKEN=你的理杏仁Token
```

> Token 获取：登录 [lixinger.com](https://www.lixinger.com) → 个人中心 → API Token

akshare 不需要 Token，直接可用。

---

## 命令一览

所有命令在 `backend/` 目录下执行，使用虚拟环境：

```bash
cd backend
source .venv/bin/activate   # 或 .venv/bin/python -m scripts.xxx
```

---

## 一、首次部署：历史回填

数据库建好后，第一次需要拉取完整历史数据（近 11 年）。

### 步骤 1：akshare 历史回填（收盘价 + 基础 PE/PB）

```bash
python -m scripts.fetch_daily --backfill
```

- 抓取全部指数近 11 年的日频数据
- A 股 / 港股来自 akshare，美股来自 yfinance
- 完成后自动触发理杏仁增强和分位数计算
- **耗时**：视网络情况，通常 10–30 分钟

### 步骤 2：理杏仁历史回填（PS / 股息率 / 更精确的 PE/PB）

上一步已包含理杏仁增强，如需单独重跑：

```bash
python -m scripts.fetch_daily --lixinger-enrich
```

> **注意**：理杏仁历史回填模式下，每个指数单独请求，速度较慢（受 API 频率限制）。

---

## 二、日常更新

收盘后（建议 20:00 以后）手动执行一次增量更新：

```bash
python -m scripts.fetch_daily --now
```

执行流程：
1. 查询每个指数在数据库中的最新日期
2. 从该日期次日起抓取至今（akshare + yfinance）
3. 用理杏仁批量接口补充最新一条的 PE/PB/PS/股息率
4. 重新计算所有指数的 10 年分位数（`calc_stats`）

---

## 三、仅重算分位数

当数据已齐全，只需更新 `index_stats`（如修改了计算逻辑）：

```bash
python -m scripts.calc_stats
```

---

## 四、补充历史 PE/PB 空值

如果历史行情已入库但 PE/PB 为空（akshare 当时未返回），可单独补充：

```bash
python -m scripts.fetch_daily --fix-pe
```

---

## 五、从缓存回填（lixinger_fundamentals → daily_metrics）

如果之前通过其他方式将理杏仁数据缓存进了 `lixinger_fundamentals` 表，可一键回填到 `daily_metrics`：

```bash
python -m scripts.fetch_daily --backfill-cache
```

> 这是一次性操作，用于数据迁移场景。

---

## 字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| `close` | akshare / yfinance | 收盘点位 |
| `pe` | akshare（优先）/ 理杏仁补充 | PE-TTM，市值加权 |
| `pb` | akshare（优先）/ 理杏仁补充 | PB，市值加权 |
| `ps` | 理杏仁独有 | PS-TTM，市值加权 |
| `dyr` | 理杏仁独有 | 股息率，原始小数（如 0.03 = 3%） |

---

## 常见问题

**`LIXINGER_TOKEN 未配置，跳过理杏仁增强`**
检查 `backend/.env` 是否有 `LIXINGER_TOKEN=` 字段且值不为空。

**某指数 PE/PB 全为空**
优先检查 akshare 是否支持该指数的估值数据，再尝试 `--fix-pe` 或 `--lixinger-enrich`。

**`DataFetchError` 频率限制**
理杏仁 API 有调用频率限制，历史回填时若报错可稍等片刻后重试，脚本会跳过已失败的指数不影响其他数据。

**分位数显示为 `—`（N/A）**
`calc_stats` 要求单个指数至少有 250 个交易日的数据才计算分位数。历史数据不足时正常，补充历史后重跑 `calc_stats` 即可。
