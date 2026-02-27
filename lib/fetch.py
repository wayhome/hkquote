import contextlib
import io
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor


def _fetch_one(symbol: str) -> dict | None:
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            hist = ticker.history(period="5d", interval="1h")

        price = info.last_price
        prev_close = info.previous_close
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
        volume = getattr(info, "last_volume", 0) or 0
        market_cap = getattr(info, "market_cap", 0) or 0

        spark = []
        if not hist.empty:
            spark = hist["Close"].dropna().tolist()

        return {
            "price": price,
            "change_pct": change_pct,
            "volume": volume,
            "market_cap": market_cap,
            "spark": spark,
        }
    except Exception:
        return None


def fetch_all(stocks: list) -> dict:
    symbols = [s[2] for s in stocks]
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(_fetch_one, symbols))
    return dict(zip(symbols, results))


def fetch_indices(index_symbols: list) -> dict:
    def _fetch_index(item):
        sym, name = item
        d = _fetch_one(sym)
        return sym, d

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(_fetch_index, index_symbols))
    return dict(results)
