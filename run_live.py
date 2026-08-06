from datetime import datetime

import pandas as pd
import yfinance as yf


WATCH_LIST = [
    "0050.TW",
    "2330.TW",
    "2454.TW",
    "2882.TW",
]


def flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns for a single ticker."""

    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.get_level_values(0)

    return data


def fetch_previous_close(ticker: str) -> float | None:
    """Fetch the most recent completed daily close before today."""

    daily = yf.download(
        ticker,
        period="5d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if daily.empty:
        return None

    daily = flatten_columns(daily)
    daily = daily.dropna(subset=["Close"])

    if len(daily) < 2:
        return None

    # The final daily row may represent today's still-open session.
    return float(daily.iloc[-2]["Close"])


def fetch_live_snapshot(ticker: str) -> dict:
    """Fetch one near-live 5-minute market snapshot."""

    try:
        intraday = yf.download(
            ticker,
            period="1d",
            interval="5m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if intraday.empty:
            return {
                "ticker": ticker,
                "status": "NO DATA",
                "time": "-",
                "price": None,
                "previous_close": None,
                "change": None,
                "change_pct": None,
                "volume": None,
            }

        intraday = flatten_columns(intraday)
        intraday = intraday.dropna(subset=["Close"])

        if intraday.empty:
            raise ValueError("Close column contains no valid values.")

        latest_price = float(intraday.iloc[-1]["Close"])
        previous_close = fetch_previous_close(ticker)

        change = None
        change_pct = None

        if previous_close is not None and previous_close != 0:
            change = latest_price - previous_close
            change_pct = change / previous_close * 100

        total_volume = int(intraday["Volume"].fillna(0).sum())
        latest_time = intraday.index[-1]

        return {
            "ticker": ticker,
            "status": "OK",
            "time": latest_time.strftime("%Y-%m-%d %H:%M"),
            "price": latest_price,
            "previous_close": previous_close,
            "change": change,
            "change_pct": change_pct,
            "volume": total_volume,
        }

    except Exception as error:
        return {
            "ticker": ticker,
            "status": f"ERROR: {error}",
            "time": "-",
            "price": None,
            "previous_close": None,
            "change": None,
            "change_pct": None,
            "volume": None,
        }


def print_snapshot(snapshot: dict) -> None:
    """Print one formatted market snapshot."""

    print("-" * 58)
    print(f"Ticker          : {snapshot['ticker']}")
    print(f"Status          : {snapshot['status']}")
    print(f"Latest Time     : {snapshot['time']}")

    if snapshot["price"] is not None:
        print(f"Latest Price    : {snapshot['price']:.2f}")

    if snapshot["previous_close"] is not None:
        print(f"Previous Close  : {snapshot['previous_close']:.2f}")

    if snapshot["change_pct"] is not None:
        direction = "🟢" if snapshot["change_pct"] >= 0 else "🔴"

        print(
            f"Daily Change    : {direction} "
            f"{snapshot['change']:+.2f} "
            f"({snapshot['change_pct']:+.2f}%)"
        )

    if snapshot["volume"] is not None:
        print(f"Volume          : {snapshot['volume']:,}")


def main() -> None:
    print("\n🌅 MORNING LIGHT — LIVE PILOT v0.2")
    print(f"Run Time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("Benchmark: Latest price versus previous close")
    print("Mode: One-time 5-minute near-live snapshot")

    for ticker in WATCH_LIST:
        snapshot = fetch_live_snapshot(ticker)
        print_snapshot(snapshot)

    print("-" * 58)
    print("✅ Live snapshot v0.2 completed.")


if __name__ == "__main__":
    main()