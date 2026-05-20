# 数据源说明

## 数据源概览

| 数据源 | 覆盖市场 | 费用 | 稳定性 | 当前状态 |
|--------|---------|------|--------|---------|
| akshare | A股、港股 | 免费 | 中（依赖第三方） | 主要源 |
| yfinance | 美股、部分港股 | 免费 | 中（Yahoo Finance） | 主要源 |
| tushare Pro | A股 | 积分制（部分免费） | 高 | 预留扩展 |
| 同花顺/东方财富 | A股、港股 | 付费 | 高 | 预留扩展 |

---

## Provider 接口定义

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

@dataclass
class DailyMetrics:
    index_code: str
    date: date
    close: float | None
    pe: float | None       # PE TTM，可能为空（如亏损指数）
    pb: float | None
    source: str            # 'akshare' / 'yfinance' / ...

class DataProvider(ABC):
    @abstractmethod
    def get_daily_metrics(self, code: str, market: str) -> DailyMetrics:
        """获取单个指数今日数据"""
        ...

    @abstractmethod
    def get_history(
        self, code: str, market: str, start_date: date
    ) -> list[DailyMetrics]:
        """获取指定起始日期至今的历史数据"""
        ...
```

---

## AkshareProvider — A股 / 港股

### A股指数 PE/PB

akshare 提供 `stock_a_pe` 等接口，但各接口覆盖的指数不同，需按指数类型选择正确接口：

| 指数类型 | akshare 接口 | 备注 |
|---------|-------------|------|
| 宽基（沪深300等） | `index_value_hist_funddb` | 有完整PE/PB历史 |
| 中证行业 | `sw_index_third_info` | 申万三级行业 |
| 创业板/科创板 | `stock_zh_index_daily` + 手动计算 | PE 需自行计算 |

### 港股指数

| 指数 | akshare 接口 | 备注 |
|------|-------------|------|
| 恒生指数 | `stock_hk_index_daily_em` | 东财源，PE 数据较全 |
| 恒生科技 | 同上 | |
| 国企指数 | 同上 | |

### 数据质量问题

- PE 为负（指数整体亏损）：存 `NULL`，分位数计算时排除
- 停牌日：无数据，不补填，保持空缺
- 历史数据回测：部分指数上市时间短（< 1 年），标记为"数据不足"，不计算分位数
- 数据延迟：akshare 通常在 T+1 晚上可获取 T 日数据，抓取时间设在 20:00

---

## YFinanceProvider — 美股

### 使用方式

```python
import yfinance as yf

ticker = yf.Ticker("^GSPC")  # 标普500
hist = ticker.history(period="10y")
info = ticker.info  # 包含 trailingPE, priceToBook
```

### 代码映射（部分）

| 指数名称 | Yahoo 代码 |
|---------|-----------|
| 标普 500 | `^GSPC` |
| 纳斯达克 100 | `^NDX` |
| 道琼斯 | `^DJI` |
| 罗素 2000 | `^RUT` |
| 费城半导体 | `^SOX` |

### 数据质量问题

- PE 数据来自 `ticker.info`，部分指数（如 ^RUT）PE 不准确
- yfinance 偶发 429 限速，需加重试和随机延迟
- 美股 PE 历史数据质量弱于 A股，分位数计算结果仅供参考

---

## 数据流

```
定时任务（每日 20:00）
  │
  ├── AkshareProvider.get_daily_metrics()  → A股/港股
  ├── YFinanceProvider.get_daily_metrics() → 美股
  │
  ├── 写入 daily_metrics 表（带 source 字段）
  │
  └── calc_stats.py
        ├── 读取每个指数近 10 年 daily_metrics
        ├── 计算 PE/PB 历史分位数
        └── 更新 index_stats 表
```

---

## 新增数据源流程

1. 在 `backend/providers/` 新建文件，实现 `DataProvider` 抽象类
2. 在 `backend/providers/composite.py` 的 `routing` 字典中注册
3. 在 `docs/data-sources.md` 补充字段映射说明
4. 写 `tests/test_providers.py` 中对应的单元测试

---

## 数据覆盖范围（指数列表）

指数主数据由 `scripts/seed_indices.py` 初始化写入数据库。

初始覆盖（Phase 2）：A股约 50 个主要宽基 + 行业指数

完整列表维护在代码中（`scripts/seed_indices.py`），不在此文档重复。
