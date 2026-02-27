from datetime import datetime
from io import StringIO
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel

SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _spark(values: list) -> str:
    if not values or len(values) < 2:
        return "─" * 8
    mn, mx = min(values), max(values)
    if mx == mn:
        return "─" * 8
    normalized = [(v - mn) / (mx - mn) for v in values]
    chars = [SPARK_CHARS[int(n * 7)] for n in normalized]
    return "".join(chars[-12:])


def _human(num: float) -> str:
    if not num:
        return "-"
    for suffix, threshold in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if abs(num) >= threshold:
            return f"{num / threshold:.2f}{suffix}"
    return f"{num:.0f}"


def _change_text(pct: float | None) -> Text:
    if pct is None:
        return Text("-", style="dim")
    s = f"{pct:+.2f}%"
    if pct > 0:
        return Text(s, style="bold green")
    elif pct < 0:
        return Text(s, style="bold red")
    return Text(s, style="dim")


def render_ansi(stocks: list, data: dict, indices: dict, index_symbols: list) -> str:
    """Render the HK stock table as an ANSI string."""
    sio = StringIO()
    console = Console(file=sio, force_terminal=True, width=100)

    # Index header
    parts = []
    for sym, name in index_symbols:
        d = indices.get(sym)
        if not d:
            continue
        pct = d["change_pct"]
        arrow = "▲" if pct >= 0 else "▼"
        color = "green" if pct >= 0 else "red"
        parts.append(
            f"[bold]{name}[/bold]  [cyan]{d['price']:,.2f}[/cyan]  "
            f"[{color}]{arrow} {pct:+.2f}%[/{color}]"
        )

    header_text = "     ".join(parts) if parts else "获取指数数据失败"
    console.print(
        Panel(
            header_text,
            title="[bold yellow]港股实时行情[/bold yellow]",
            border_style="dim yellow",
        )
    )

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold yellow")
    table.add_column("代码", style="cyan", width=6, no_wrap=True)
    table.add_column("名称", width=12, no_wrap=True)
    table.add_column("现价(HKD)", justify="right", width=10)
    table.add_column("涨跌幅", justify="right", width=9)
    table.add_column("成交量", justify="right", width=8)
    table.add_column("市值", justify="right", width=10)
    table.add_column("走势(5日)", width=14, no_wrap=True)

    for code, name, symbol in stocks:
        d = data.get(symbol)
        if not d:
            table.add_row(code, name, "-", "-", "-", "-", Text("─" * 8, style="dim"))
            continue

        price = f"{d['price']:.3f}" if d["price"] else "-"
        pct = d["change_pct"]
        spark_str = _spark(d["spark"])
        spark_color = "green" if pct >= 0 else "red"

        table.add_row(
            code,
            name,
            Text(price, style="cyan"),
            _change_text(pct),
            _human(d["volume"]),
            _human(d["market_cap"]),
            Text(spark_str, style=spark_color),
        )

    console.print(table)
    console.print(
        f"[dim]更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  "
        f"数据来源: Yahoo Finance[/dim]\n"
    )

    return sio.getvalue()
