"""
HTTP server for HK stock market quotes.

  curl localhost:8080              # top 30 stocks
  curl localhost:8080?n=10         # top 10 stocks
  curl localhost:8080/0700         # Tencent chart (1mo)
  curl localhost:8080/0700@5d      # Tencent 5-day chart
  curl localhost:8080/0700@1y      # Tencent 1-year chart
"""

import os
import time
import threading

from flask import Flask, request
from lib.stocks import HSI_STOCKS, INDEX_SYMBOLS
from lib.fetch import fetch_all, fetch_indices
from lib.render import render_ansi
from lib.chart import render_chart, DEFAULT_PERIOD, SUPPORTED_PERIODS

app = Flask(__name__)

CACHE_TTL = 60  # seconds

_cache = {"ansi": None, "ts": 0}
_lock = threading.Lock()


def _is_curl(user_agent: str) -> bool:
    plaintext = ["curl", "wget", "fetch", "httpie", "python-requests", "lwp-request"]
    return any(x in user_agent.lower() for x in plaintext)


def _to_html(ansi: str, title: str = "港股实时行情") -> str:
    try:
        from ansi2html import Ansi2HTMLConverter
        conv = Ansi2HTMLConverter(dark_bg=True, title=title)
        return conv.convert(ansi)
    except ImportError:
        return f"<pre>{ansi}</pre>"


def _get_table(top: int) -> str:
    with _lock:
        now = time.time()
        if _cache["ansi"] is None or now - _cache["ts"] > CACHE_TTL:
            stocks = HSI_STOCKS[:top]
            stock_data = fetch_all(stocks)
            index_data = fetch_indices(INDEX_SYMBOLS)
            _cache["ansi"] = render_ansi(stocks, stock_data, index_data, INDEX_SYMBOLS)
            _cache["ts"] = now
        return _cache["ansi"]


@app.route("/")
def index():
    ua = request.headers.get("User-Agent", "")
    top = int(request.args.get("n", 30))
    ansi = _get_table(top)
    if _is_curl(ua):
        return ansi, 200, {"Content-Type": "text/plain; charset=utf-8"}
    return _to_html(ansi)


@app.route("/<path:topic>")
def stock_chart(topic):
    ua = request.headers.get("User-Agent", "")

    # Parse "0700" or "0700@1mo"
    if "@" in topic:
        code, period = topic.split("@", 1)
    else:
        code, period = topic, DEFAULT_PERIOD

    ansi = render_chart(code.strip(), period.strip())

    if _is_curl(ua):
        return ansi, 200, {"Content-Type": "text/plain; charset=utf-8"}
    return _to_html(ansi, title=f"{code.upper()} 港股行情")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting HK markets server on port {port}")
    print(f"  curl localhost:{port}           # 行情列表")
    print(f"  curl localhost:{port}/0700       # 个股走势 (默认1mo)")
    print(f"  curl localhost:{port}/0700@5d    # 时间范围: {SUPPORTED_PERIODS}")
    app.run(host="0.0.0.0", port=port, threaded=True)
