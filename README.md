# hkquote

港股实时行情查看器，通过 `curl` 访问终端表格和个股走势图。

Inspired by [rate.sx](https://github.com/chubin/rate.sx).

## 使用

启动服务：

```bash
PORT=8080 uv run python srv.py
```

### 行情列表

```bash
curl localhost:8080          # 默认显示前 30 只
curl localhost:8080?n=10     # 显示前 N 只
```

```
╭──────────────────── 港股实时行情 ────────────────────╮
│ 恒生指数  26,648  ▲ +1.01%                          │
╰──────────────────────────────────────────────────────╯

  代码   名称         现价(HKD)   涨跌幅    成交量      市值   走势(5日)
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  0700   腾讯控股       521.000   +1.76%    19.67M     4.70T   ▂▂▁▁▂▄▄▃▃▃
  9988   阿里巴巴       144.300   +0.91%    51.59M     2.76T   ▂▂▁▁▁▂▂▁▂▁
  ...
```

### 个股走势

```bash
curl localhost:8080/0700          # 默认 1 个月
curl localhost:8080/0700@5d       # 5 天
curl localhost:8080/0700@3mo      # 3 个月
curl localhost:8080/0700@1y       # 1 年
```

支持时间范围：`1d` `5d` `1mo` `3mo` `6mo` `1y` `2y`

```
▶ 0700 腾讯控股 ▶  Tue 27 +1个月  -14.09%

  │      625.00
  │ ⡇ ⢀⠜⠉⠉⠉⠉⢆
  │ ⡇⢀⠎     ⠈⢆
  │ ⣧⠃       ⠈⢆
  │              ⠑⠢⡀
  │                ⠈⢆
  │                 ⠈⢆
  │                  ⠈⡆
  │                   ⠸⡀
  │                    ⢣
  │                     ⢇
  │                     ⠘⡄
  │                      ⠱⠤⠔⠒⠒⡄     ⡰⠑⢄
  │                           ⠈⢢  ⢀⠜   ⠑⢄
  │                                         ⠱⡀
  │                                          ⠘⢄
  │                                            ⠣⣀⡀    ⢀⡀
  │                                              ⠈⠑⠒⠊⠉⠁⠈⢆
  │                                                      ⠣⡀
  │                                                       ⠑⠎
  │                                                              510.50
  └────────────────────────────────────────────────────────────────────

begin: 607.00 (Tue 27) // end: 521.50 (Fri 27)
high: 625.00 (Thu 29)  // low: 510.50 (Fri 27)
avg: 556.98 // median: 548.00 // change: -85.500 (-14.09%)
```

浏览器访问会自动转换为 HTML。

## 安装

```bash
git clone <repo>
cd markets
uv sync
```

## 项目结构

```
markets/
├── srv.py          # Flask HTTP 服务入口
├── main.py         # CLI 直接运行
└── lib/
    ├── stocks.py   # 港股列表（HSI 成分股）
    ├── fetch.py    # yfinance 数据获取（并发）
    ├── render.py   # 行情列表渲染（rich）
    └── chart.py    # 个股走势图（diagram + spectrum 渐变）
```

## 数据来源

[Yahoo Finance](https://finance.yahoo.com) via [yfinance](https://github.com/ranaroussi/yfinance)

## License

MIT
