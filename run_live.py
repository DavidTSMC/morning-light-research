from datetime import datetime

import pandas as pd
import yfinance as yf


WATCH_LIST = [
    "0050.TW",
    "2330.TW",
    "2454.TW",
    "2882.TW",
]

FRESH_LIMIT_MINUTES = 10
DELAYED_LIMIT_MINUTES = 30

WR_PERIOD = 5
WR_TRIGGER_LEVEL = -80.0


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

    # The latest daily row may represent today's unfinished session.
    return float(daily.iloc[-2]["Close"])


def calculate_quote_age(latest_time: pd.Timestamp) -> float:
    """Return quote age in minutes."""

    latest_time = pd.Timestamp(latest_time)

    if latest_time.tzinfo is not None:
        current_time = pd.Timestamp.now(tz=latest_time.tz)
    else:
        current_time = pd.Timestamp.now()

    age_minutes = (
        current_time - latest_time
    ).total_seconds() / 60

    return max(0.0, age_minutes)


def classify_freshness(
    age_minutes: float,
) -> tuple[str, str]:
    """Classify market-data freshness."""

    if age_minutes <= FRESH_LIMIT_MINUTES:
        return (
            "🟢 FRESH",
            "Suitable for live research monitoring",
        )

    if age_minutes <= DELAYED_LIMIT_MINUTES:
        return (
            "🟡 DELAYED",
            "Research only — do not use for execution",
        )

    return (
        "🔴 STALE",
        "Outdated data — refresh before interpretation",
    )


def calculate_wr(
    data: pd.DataFrame,
    period: int = WR_PERIOD,
) -> pd.Series:
    """
    Calculate Williams %R.

    Formula:
        WR = -100 * (Highest High - Close)
                    / (Highest High - Lowest Low)

    Range:
        0 to -100
    """

    highest_high = data["High"].rolling(
        window=period,
        min_periods=period,
    ).max()

    lowest_low = data["Low"].rolling(
        window=period,
        min_periods=period,
    ).min()

    price_range = highest_high - lowest_low

    wr = -100 * (
        highest_high - data["Close"]
    ) / price_range

    # A zero price range would cause division by zero.
    wr = wr.where(price_range != 0)

    return wr


def classify_wr(
    current_wr: float,
    previous_wr: float,
) -> dict:
    """Interpret the latest WR5 movement."""

    change = current_wr - previous_wr

    if change > 0.01:
        direction = "↑"
    elif change < -0.01:
        direction = "↓"
    else:
        direction = "→"

    crossed_trigger = (
        previous_wr <= WR_TRIGGER_LEVEL
        and current_wr > WR_TRIGGER_LEVEL
    )

    if crossed_trigger:
        status = "🟢 TRIGGERED"
        explanation = "WR5 crossed above -80"

    elif current_wr <= WR_TRIGGER_LEVEL and change > 0:
        status = "🟡 RECOVERING"
        explanation = "Oversold area is improving"

    elif current_wr <= WR_TRIGGER_LEVEL:
        status = "🔴 OVERSOLD"
        explanation = "Still below the -80 trigger level"

    else:
        status = "⚪ NEUTRAL"
        explanation = "WR5 is above the oversold zone"

    distance = max(
        0.0,
        WR_TRIGGER_LEVEL - current_wr,
    )

    return {
        "previous": previous_wr,
        "current": current_wr,
        "change": change,
        "direction": direction,
        "status": status,
        "explanation": explanation,
        "trigger": WR_TRIGGER_LEVEL,
        "distance": distance,
        "crossed_trigger": crossed_trigger,
    }


def build_wr_snapshot(
    intraday: pd.DataFrame,
) -> dict | None:
    """Build latest and previous WR5 observations."""

    required_rows = WR_PERIOD + 1

    if len(intraday) < required_rows:
        return None

    wr_series = calculate_wr(
        intraday,
        period=WR_PERIOD,
    ).dropna()

    if len(wr_series) < 2:
        return None

    previous_wr = float(wr_series.iloc[-2])
    current_wr = float(wr_series.iloc[-1])

    return classify_wr(
        current_wr=current_wr,
        previous_wr=previous_wr,
    )


def empty_snapshot(
    ticker: str,
    status: str,
    freshness: str,
    safety_notice: str,
) -> dict:
    """Return a consistent empty result."""

    return {
        "ticker": ticker,
        "status": status,
        "time": "-",
        "price": None,
        "previous_close": None,
        "change": None,
        "change_pct": None,
        "volume_shares": None,
        "volume_lots": None,
        "quote_age": None,
        "freshness": freshness,
        "safety_notice": safety_notice,
        "wr": None,
    }


def fetch_live_snapshot(ticker: str) -> dict:
    """Fetch one near-live 5-minute snapshot with WR5."""

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
            return empty_snapshot(
                ticker=ticker,
                status="NO DATA",
                freshness="🔴 UNKNOWN",
                safety_notice="No usable market data",
            )

        intraday = flatten_columns(intraday)

        required_columns = [
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in intraday.columns
        ]

        if missing_columns:
            raise ValueError(
                "Missing columns: "
                + ", ".join(missing_columns)
            )

        intraday = intraday.dropna(
            subset=["High", "Low", "Close"]
        )

        if intraday.empty:
            raise ValueError(
                "Intraday price columns contain no valid values."
            )

        latest_price = float(
            intraday.iloc[-1]["Close"]
        )

        previous_close = fetch_previous_close(ticker)

        change = None
        change_pct = None

        if (
            previous_close is not None
            and previous_close != 0
        ):
            change = latest_price - previous_close
            change_pct = (
                change / previous_close * 100
            )

        volume_shares = int(
            intraday["Volume"].fillna(0).sum()
        )

        volume_lots = volume_shares / 1000

        latest_time = pd.Timestamp(
            intraday.index[-1]
        )

        quote_age = calculate_quote_age(
            latest_time
        )

        freshness, safety_notice = (
            classify_freshness(quote_age)
        )

        wr_snapshot = build_wr_snapshot(
            intraday
        )

        return {
            "ticker": ticker,
            "status": "OK",
            "time": latest_time.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "price": latest_price,
            "previous_close": previous_close,
            "change": change,
            "change_pct": change_pct,
            "volume_shares": volume_shares,
            "volume_lots": volume_lots,
            "quote_age": quote_age,
            "freshness": freshness,
            "safety_notice": safety_notice,
            "wr": wr_snapshot,
        }

    except Exception as error:
        return empty_snapshot(
            ticker=ticker,
            status=f"ERROR: {error}",
            freshness="🔴 ERROR",
            safety_notice=(
                "Snapshot could not be validated"
            ),
        )


def print_wr(wr_snapshot: dict | None) -> None:
    """Print the live WR5 analysis."""

    print("\n📡 LIVE TECHNICAL INDICATOR")

    if wr_snapshot is None:
        print("WR5             : NOT AVAILABLE")
        print(
            "Reason          : Insufficient valid "
            "5-minute bars"
        )
        return

    print("Indicator       : Williams %R")
    print("Timeframe       : 5-minute bars")
    print(f"Period          : {WR_PERIOD}")

    print(
        f"WR5 Previous    : "
        f"{wr_snapshot['previous']:.2f}"
    )

    print(
        f"WR5 Current     : "
        f"{wr_snapshot['current']:.2f} "
        f"{wr_snapshot['direction']}"
    )

    print(
        f"WR5 Change      : "
        f"{wr_snapshot['change']:+.2f}"
    )

    print(
        f"WR5 Status      : "
        f"{wr_snapshot['status']}"
    )

    print(
        f"Next Trigger    : "
        f"WR5 > {WR_TRIGGER_LEVEL:.0f}"
    )

    print(
        f"Distance        : "
        f"{wr_snapshot['distance']:.2f} pts"
    )

    print(
        f"Explanation     : "
        f"{wr_snapshot['explanation']}"
    )


def print_snapshot(snapshot: dict) -> None:
    """Print one formatted market snapshot."""

    print("-" * 68)

    print(
        f"Ticker          : "
        f"{snapshot['ticker']}"
    )

    print(
        f"Status          : "
        f"{snapshot['status']}"
    )

    print(
        f"Latest Time     : "
        f"{snapshot['time']}"
    )

    if snapshot["price"] is not None:
        print(
            f"Latest Price    : "
            f"{snapshot['price']:.2f}"
        )

    if snapshot["previous_close"] is not None:
        print(
            f"Previous Close  : "
            f"{snapshot['previous_close']:.2f}"
        )

    if snapshot["change_pct"] is not None:
        direction = (
            "🟢"
            if snapshot["change_pct"] >= 0
            else "🔴"
        )

        print(
            f"Daily Change    : {direction} "
            f"{snapshot['change']:+.2f} "
            f"({snapshot['change_pct']:+.2f}%)"
        )

    if snapshot["volume_shares"] is not None:
        print(
            f"Volume Shares   : "
            f"{snapshot['volume_shares']:,}"
        )

        print(
            f"Volume Lots     : "
            f"{snapshot['volume_lots']:,.0f} 張"
        )

    if snapshot["quote_age"] is not None:
        print(
            f"Quote Age       : "
            f"{snapshot['quote_age']:.1f} minutes"
        )

    print(
        f"Data Freshness  : "
        f"{snapshot['freshness']}"
    )

    print(
        f"Safety Notice   : "
        f"{snapshot['safety_notice']}"
    )

    print_wr(snapshot["wr"])


def main() -> None:
    """Run one complete Morning Light live scan."""

    print(
        "\n🌅 MORNING LIGHT — LIVE PILOT v0.3"
    )

    print(
        f"Run Time: "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    print(
        "Mode: Near-live snapshot "
        "with Freshness Guard + Live WR5"
    )

    print(
        "WR Definition: 5 periods "
        "on 5-minute bars"
    )

    snapshots = []

    for ticker in WATCH_LIST:
        snapshot = fetch_live_snapshot(ticker)
        snapshots.append(snapshot)
        print_snapshot(snapshot)

    delayed_count = sum(
        snapshot["freshness"] != "🟢 FRESH"
        for snapshot in snapshots
    )

    wr_count = sum(
        snapshot["wr"] is not None
        for snapshot in snapshots
    )

    triggered_count = sum(
        bool(
            snapshot["wr"]
            and snapshot["wr"]["crossed_trigger"]
        )
        for snapshot in snapshots
    )

    print("-" * 68)
    print("🌅 LIVE WR5 SUMMARY")
    print(f"Stocks scanned  : {len(snapshots)}")
    print(f"WR5 calculated  : {wr_count}")
    print(f"WR5 triggered   : {triggered_count}")

    if delayed_count == 0:
        print(
            "Freshness Guard : "
            "✅ All snapshots passed"
        )
    else:
        print(
            f"Freshness Guard : "
            f"⚠️ {delayed_count} delayed, stale, "
            "or unavailable"
        )

        print(
            "Safety          : "
            "Research use only — not for execution"
        )

    print(
        "✅ Live WR5 Engine v0.3 completed."
    )


if __name__ == "__main__":
    main()