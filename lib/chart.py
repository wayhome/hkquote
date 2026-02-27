"""
Individual stock chart — styled after rate.sx.
  curl localhost:8080/0700
  curl localhost:8080/0700@5d
  curl localhost:8080/0700@1y
"""

import contextlib
import io
import os
from datetime import datetime

import diagram
from colorama import Fore, Back, Style
import yfinance as yf

from lib.stocks import HSI_STOCKS

_CODE_TO_NAME = {code: name for code, name, _ in HSI_STOCKS}

PERIOD_MAP = {
    "1d":  ("1d",  "5m",  "1天"),
    "5d":  ("5d",  "1h",  "5天"),
    "1mo": ("1mo", "1d",  "1个月"),
    "3mo": ("3mo", "1d",  "3个月"),
    "6mo": ("6mo", "1wk", "6个月"),
    "1y":  ("1y",  "1wk", "1年"),
    "2y":  ("2y",  "1mo", "2年"),
}
DEFAULT_PERIOD = "1mo"
SUPPORTED_PERIODS = " | ".join(PERIOD_MAP.keys())

# Register spectrum-reversed palette (same trick as rate.sx)
diagram.PALETTE["spectrum-reversed"] = {
    0x010: diagram.PALETTE["spectrum"][0x010][::-1],
    0x100: diagram.PALETTE["spectrum"][0x100][::-1],
}


def _normalize_code(raw: str) -> str:
    raw = raw.strip().upper()
    if raw in _CODE_TO_NAME:
        return raw
    padded = raw.zfill(4)
    return padded


def _format_val(v: float) -> str:
    if v >= 1000:
        return f"{v:.1f}"
    if v >= 100:
        return f"{v:.2f}"
    return f"{v:.3f}"


def _align_label(label: str, idx: int, total: int, width: int = 80) -> str:
    pos = int(width * idx / max(total - 1, 1))
    pos = max(0, pos - len(label) // 2)
    return " " * pos + label


def _make_diagram(ticks: list[float], width: int = 80, height: int = 25) -> str:
    class _Opt:
        axis = False
        batch = None
        color = True
        encoding = None
        function = None
        height = None
        keys = None
        legend = None
        palette = "spectrum-reversed"
        reverse = None
        sleep = None
        sort_by_column = None

    os.environ.setdefault("TERM", "xterm-256color")
    istream = [str(x) for x in ticks]
    ostream = io.BytesIO()
    size = diagram.Point((width, height))
    engine = diagram.AxisGraph(size, _Opt())
    engine.consume(istream, ostream)
    return ostream.getvalue().decode("utf-8")


def render_chart(code: str, period_key: str = DEFAULT_PERIOD, host: str = "localhost:8080") -> str:
    period_key = period_key.lower()
    if period_key not in PERIOD_MAP:
        return f"不支持的时间范围: {period_key}\n支持: {SUPPORTED_PERIODS}\n"

    period, interval, period_label = PERIOD_MAP[period_key]
    code = _normalize_code(code)
    symbol = f"{code}.HK"
    name = _CODE_TO_NAME.get(code, code)

    with contextlib.redirect_stderr(io.StringIO()):
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if code not in _CODE_TO_NAME:
            try:
                info = ticker.info
                name = info.get("shortName") or info.get("longName") or code
            except Exception:
                name = code

    if hist.empty:
        return f"未找到股票数据: {code} ({symbol})\n"

    closes = hist["Close"].dropna().tolist()
    highs  = hist["High"].dropna().tolist()
    lows   = hist["Low"].dropna().tolist()
    times  = hist.index.tolist()

    if not closes:
        return f"无价格数据: {code}\n"

    begin      = closes[0]
    end        = closes[-1]
    high       = max(highs)
    low        = min(lows)
    avg        = sum(closes) / len(closes)
    median     = sorted(closes)[len(closes) // 2]
    change     = end - begin
    change_pct = change / begin * 100

    hi_idx = highs.index(high)
    lo_idx = lows.index(low)

    chg_color = Fore.GREEN if change >= 0 else Fore.RED
    arrow     = "▲" if change >= 0 else "▼"

    # ── Header (rate.sx style) ──────────────────────────────────────────
    t_begin = times[0].strftime("%a %d")
    out  = "\n"
    out += Back.WHITE + Fore.BLACK + f"▶ {code} {name} " + Style.RESET_ALL
    out += Fore.WHITE + "▶" + Style.RESET_ALL
    out += f"  {t_begin} +{period_label}"
    out += f"  {chg_color}{change_pct:+.2f}%{Style.RESET_ALL}"
    out += "\n\n"

    # ── Diagram ─────────────────────────────────────────────────────────
    chart_str = _make_diagram(closes, width=80, height=25)
    chart_lines = chart_str.splitlines()

    high_label = _align_label(_format_val(high), hi_idx, len(closes))
    low_label  = _align_label(_format_val(low),  lo_idx, len(closes))

    out += f"  │ {high_label}\n"
    for line in chart_lines:
        out += f"  │ {line}\n"
    out += f"  │ {low_label}\n"
    out += "  └" + "─" * 80 + "\n"

    # ── Footer ──────────────────────────────────────────────────────────
    t_end = times[-1].strftime("%a %d %H:%M")
    t_beg = times[0].strftime("%a %d %H:%M")
    t_hi  = times[hi_idx].strftime("%a %d %H:%M")
    t_lo  = times[lo_idx].strftime("%a %d %H:%M")

    dim = Style.DIM
    rst = Style.RESET_ALL

    out += f"\n{dim}begin:{rst} {_format_val(begin)} ({t_beg})"
    out += f"{dim} // {rst}"
    out += f"{dim}end:{rst} {_format_val(end)} ({t_end})\n"

    out += f"{dim}high:{rst} {Fore.GREEN}{_format_val(high)}{rst} ({t_hi})"
    out += f"{dim} // {rst}"
    out += f"{dim}low:{rst} {Fore.RED}{_format_val(low)}{rst} ({t_lo})\n"

    out += f"{dim}avg:{rst} {_format_val(avg)}"
    out += f"{dim} // {rst}"
    out += f"{dim}median:{rst} {_format_val(median)}"
    out += f"{dim} // {rst}"
    out += f"{dim}change:{rst} {chg_color}{change:+.3f}{rst} ({chg_color}{change_pct:+.2f}%{rst})\n"

    out += (
        f"\n{dim}用法: curl {host}/<代码>[@时间范围]  "
        f"时间范围: {SUPPORTED_PERIODS}{rst}\n\n"
    )
    return out
