# 理杏仁数据拉取说明

## 前提：配置 Token

在 `backend/.env` 中填入理杏仁 Token：

```
LIXINGER_TOKEN=你的理杏仁Token
```

> Token 获取：登录 [lixinger.com](https://www.lixinger.com) → 个人中心 → API Token

---

## 两种拉取场景

### 场景一：单个指数拉取 10 年历史数据

适用于**首次部署**或某只指数的历史回填。

```bash
cd backend
# 全部 A 股指数
.venv/bin/python -m scripts.fetch_daily --lixinger-enrich

# 指定指数（空格分隔）
.venv/bin/python -m scripts.fetch_daily --lixinger-enrich --codes 000905
```

- 对指定（或全部）A 股指数**逐个**发请求，带完整日期区间（近 11 年）
- API 限制：传日期区间时每次只能请求 **1 个**指数
- 数据写入 `daily_metrics`（pe / pb / ps / dyr 字段）
- 原始响应同时缓存到 `lixinger_fundamentals` 表

---

### 场景二：100 个指数拉取单天数据

适用于**每日收盘后**的增量更新。

```bash
cd backend
python -m scripts.fetch_daily --now
```

- 批量请求当天所有指数的最新估值，每次最多 **100 个**指数
- 完成后自动触发分位数重算（`calc_stats`）

---

## 分位数计算

拉取完数据后，单独重算分位数：

```bash
python -m scripts.calc_stats
```

> `--now` 和 `--lixinger-enrich` 执行完毕后会自动触发，通常无需手动运行。
