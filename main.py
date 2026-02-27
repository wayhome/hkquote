import argparse

from lib.stocks import HSI_STOCKS, INDEX_SYMBOLS
from lib.fetch import fetch_all, fetch_indices
from lib.render import render_ansi


def main():
    import argparse
    parser = argparse.ArgumentParser(description="港股实时行情查看器")
    parser.add_argument("--top", type=int, default=30, help="显示前N只股票 (默认: 30)")
    args = parser.parse_args()

    stocks = HSI_STOCKS[: args.top]
    print("正在获取行情数据...", end="\r", flush=True)

    stock_data = fetch_all(stocks)
    index_data = fetch_indices(INDEX_SYMBOLS)

    print(" " * 30, end="\r")
    print(render_ansi(stocks, stock_data, index_data, INDEX_SYMBOLS), end="")


if __name__ == "__main__":
    main()
