# 小红书图片生成工具

每日从数据库读取最新估值数据，生成可直接发布到小红书的 1080×1440 PNG 图片。

## 图片类型

| 类型 | 文件名示例 | 内容 |
|------|-----------|------|
| 每日汇总 | `summary_20260521.png` | 多只指数的 PE/PS/PB/股息率四维分位，一图速读 |
| 指数详情 | `detail_000300_20260521.png` | 单只指数的 PE/PB/PS 走势图 + 30/50/80% 分位线 |

---

## 环境准备（只需做一次）

### 1. 确认本地 `.env` 指向远程数据库

```bash
# backend/.env
DB_HOST=你的服务器IP
DB_PORT=3306
DB_USER=etf
DB_PASSWORD=你的密码
DB_NAME=etf_thermometer
```

### 2. 安装工具依赖

```bash
cd backend
.venv/bin/pip install -r requirements-tools.txt
```

### 3. 安装 Chromium（截图引擎）

```bash
.venv/bin/playwright install chromium
```

---

## 生成图片

所有命令在 `backend/` 目录下执行。

### 每日汇总图

```bash
.venv/bin/python -m scripts.generate_images --type summary
```

### 单只指数详情图

```bash
.venv/bin/python -m scripts.generate_images --type detail --code 000300
```

支持的指数代码：`000300`（沪深300）、`000016`（上证50）、`000905`（中证500）、`000852`（中证1000）

### 一键生成全部

```bash
.venv/bin/python -m scripts.generate_images --all
```

等价于生成汇总图 + 全部已配置指数的详情图。

---

## 输出位置

图片保存在项目根目录的 `output/` 文件夹：

```
output/
├── summary_20260521.png
├── detail_000300_20260521.png
├── detail_000016_20260521.png
└── ...
```

> `output/` 已加入 `.gitignore`，不会提交到 Git。

---

## 自定义配置

如需修改汇总图展示的指数列表或详情图支持的指数，编辑 `scripts/generate_images.py` 顶部的两个常量：

```python
# 每日汇总展示的指数（按顺序）
SUMMARY_CODES = ['000300', '000016', '000905', '000852', '399006', '000688', '000922']

# 支持详情图的指数
DETAIL_CODES = ['000300', '000016', '000905', '000852']
```

---

## 常见问题

**图片中字体显示异常**
模板使用 Google Fonts，生成时需要能访问外网。确认本地网络可以访问 `fonts.googleapis.com`。

**报错 `connection refused` 或 `Can't connect to MySQL`**
检查 `.env` 中的 `DB_HOST` 是否填写了服务器公网 IP，以及服务器 MySQL 的 3306 端口是否对外开放。

**某指数的 PS / 股息率显示 `—`**
该指数在数据库中暂无对应数据，需先运行理杏仁数据回填脚本：
```bash
.venv/bin/python -m scripts.fetch_daily
```


.venv/bin/python -m scripts.generate_images --v2