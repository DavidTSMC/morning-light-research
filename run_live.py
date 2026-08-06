from datetime import datetime

import pandas as pd
import yfinance as yf


WATCH_LIST = [
    "0050.TW",
    "2330.TW",
    "2454.TW",
    "2882.TW",
]


def fetch_live_snapshot(ticker: str) -> dict:
    """Fetch one near-live 5-minute snapshot for a ticker."""

    try:
        data = yf.download(
            ticker,
            period="1d",
            interval="5m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if data.empty:
            return {
                "ticker": ticker,
                "status": "NO DATA",
                "time": "-",
                "price": None,
                "change_pct": None,
            }

        # yfinance may return MultiIndex columns even for one ticker.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna(subset=["Close"])

        if data.empty:
            return {
                "ticker": ticker,
                "status": "INVALID DATA",
                "time": "-",
                "price": None,
                "change_pct": None,
            }

        latest = data.iloc[-1]
        first = data.iloc[0]

        latest_price = float(latest["Close"])
        opening_price = float(first["Open"])

        change_pct = (
            (latest_price / opening_price - 1) * 100
            if opening_price != 0
            else None
        )

        latest_time = data.index[-1]

        return {
            "ticker": ticker,
            "status": "OK",
            "time": latest_time.strftime("%Y-%m-%d %H:%M"),
            "price": latest_price,
            "change_pct": change_pct,
        }

    except Exception as error:
        return {
            "ticker": ticker,
            "status": f"ERROR: {error}",
            "time": "-",
            "price": None,
            "change_pct": None,
        }


def print_snapshot(snapshot: dict) -> None:
    """Print one formatted live snapshot."""

    print("-" * 52)
    print(f"Ticker       : {snapshot['ticker']}")
    print(f"Status       : {snapshot['status']}")
    print(f"Latest Time  : {snapshot['time']}")

    if snapshot["price"] is not None:
        print(f"Latest Price : {snapshot['price']:.2f}")

    if snapshot["change_pct"] is not None:
        direction = "🟢" if snapshot["change_pct"] >= 0 else "🔴"
        print(
            f"Intraday Move: {direction} "
            f"{snapshot['change_pct']:+.2f}%"
        )


def main() -> None:
    print("\n🌅 MORNING LIGHT — LIVE PILOT v0.1")
    print(f"Run Time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("Mode: One-time 5-minute near-live snapshot")

    for ticker in WATCH_LIST:
        snapshot = fetch_live_snapshot(ticker)
        print_snapshot(snapshot)

    print("-" * 52)
    print("✅ Live snapshot completed.")


if __name__ == "__main__":
    main()