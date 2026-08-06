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

PSY_PERIODS = (12, 24)


def flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns for one ticker."""

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

    # The latest daily row may be today's unfinished session.
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


# ============================================================
# WR ENGINE
# ============================================================

def calculate_wr(
    data: pd.DataFrame,
    period: int = WR_PERIOD,
) -> pd.Series:
    """
    Calculate Williams %R.

    WR = -100 × (Highest High - Close)
                / (Highest High - Lowest Low)

    Range: 0 to -100
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

    # Avoid division by zero when all prices are identical.
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

    if len(intraday) < WR_PERIOD + 1:
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


# ============================================================
# PSY ENGINE
# ============================================================

def calculate_psy(
    close: pd.Series,
    period: int,
) -> pd.Series:
    """
    Calculate Psychological Line (PSY).

    One rising observation occurs when:
        current close > previous close

    PSY = rising observations / period × 100
    """

    price_change = close.diff()

    rising = (
        price_change > 0
    ).astype(float)

    psy = rising.rolling(
        window=period,
        min_periods=period,
    ).sum() / period * 100

    return psy


def get_direction(
    current_value: float,
    previous_value: float,
    tolerance: float = 0.01,
) -> str:
    """Return a simple direction symbol."""

    change = current_value - previous_value

    if change > tolerance:
        return "↑"

    if change < -tolerance:
        return "↓"

    return "→"


def classify_psy(
    current_value: float,
    previous_value: float,
) -> tuple[str, str]:
    """
    Give PSY a preliminary descriptive zone.

    These labels are informational only.
    Reality Check comes before trigger-rule adoption.
    """

    direction = get_direction(
        current_value,
        previous_value,
    )

    if current_value <= 25:
        if direction == "↑":
            return (
                "🟡 LOW — RECOVERING",
                "Low participation is beginning to improve",
            )

        return (
            "🔴 LOW",
            "Few recent bars closed higher",
        )

    if current_value >= 75:
        if direction == "↓":
            return (
                "🟡 HIGH — COOLING",
                "High participation is beginning to weaken",
            )

        return (
            "🔴 HIGH",
            "Many recent bars closed higher",
        )

    return (
        "⚪ NEUTRAL",
        "PSY is inside the middle range",
    )


def build_one_psy_snapshot(
    close: pd.Series,
    period: int,
) -> dict | None:
    """Build one PSY-period result."""

    # N comparisons require at least N + 1 closing prices.
    if len(close) < period + 1:
        return None

    psy_series = calculate_psy(
        close=close,
        period=period,
    ).dropna()

    if len(psy_series) < 2:
        return None

    previous_value = float(
        psy_series.iloc[-2]
    )

    current_value = float(
        psy_series.iloc[-1]
    )

    change = current_value - previous_value

    direction = get_direction(
        current_value,
        previous_value,
    )

    status, explanation = classify_psy(
        current_value=current_value,
        previous_value=previous_value,
    )

    rising_count = int(
        round(current_value * period / 100)
    )

    return {
        "period": period,
        "previous": previous_value,
        "current": current_value,
        "change": change,
        "direction": direction,
        "rising_count": rising_count,
        "status": status,
        "explanation": explanation,
    }


def build_psy_snapshot(
    intraday: pd.DataFrame,
) -> dict:
    """Build PSY12 and PSY24 observations."""

    close = intraday["Close"].dropna()

    results = {}

    for period in PSY_PERIODS:
        results[period] = build_one_psy_snapshot(
            close=close,
            period=period,
        )

    return results


# ============================================================
# LIVE SNAPSHOT
# ============================================================

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
        "psy": {},
    }


def fetch_live_snapshot(ticker: str) -> dict:
    """Fetch one near-live snapshot with WR5 and PSY."""

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

        previous_close = fetch_previous_close(
            ticker
        )

        change = None
        change_pct = None

        if (
            previous_close is not None
            and previous_close != 0
        ):
            change = (
                latest_price - previous_close
            )

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

        psy_snapshot = build_psy_snapshot(
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
            "psy": psy_snapshot,
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


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def print_wr(
    wr_snapshot: dict | None,
) -> None:
    """Print live WR5 analysis."""

    print("\n📡 LIVE INDICATOR 1 — WR")

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


def print_one_psy(
    psy_snapshot: dict | None,
    period: int,
) -> None:
    """Print one PSY-period result."""

    label = f"PSY{period}"

    if psy_snapshot is None:
        print(f"{label:<16}: NOT AVAILABLE")
        print(
            f"{'Reason':<16}: Need at least "
            f"{period + 1} valid closes"
        )
        return

    print(
        f"{label + ' Previous':<16}: "
        f"{psy_snapshot['previous']:.2f}"
    )

    print(
        f"{label + ' Current':<16}: "
        f"{psy_snapshot['current']:.2f} "
        f"{psy_snapshot['direction']}"
    )

    print(
        f"{label + ' Change':<16}: "
        f"{psy_snapshot['change']:+.2f}"
    )

    print(
        f"{label + ' Rising':<16}: "
        f"{psy_snapshot['rising_count']}"
        f"/{period} bars"
    )

    print(
        f"{label + ' Status':<16}: "
        f"{psy_snapshot['status']}"
    )

    print(
        f"{label + ' Note':<16}: "
        f"{psy_snapshot['explanation']}"
    )


def print_psy(
    psy_snapshots: dict,
) -> None:
    """Print PSY12 and PSY24 analysis."""

    print("\n🧠 LIVE INDICATOR 2 — PSY")
    print("Indicator       : Psychological Line")
    print("Timeframe       : 5-minute bars")
    print(
        "Definition      : Rising closes / "
        "period × 100"
    )

    for period in PSY_PERIODS:
        print()
        print_one_psy(
            psy_snapshot=psy_snapshots.get(period),
            period=period,
        )


def print_snapshot(snapshot: dict) -> None:
    """Print one complete live snapshot."""

    print("-" * 70)

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
    print_psy(snapshot["psy"])


def main() -> None:
    """Run one complete Morning Light live scan."""

    print(
        "\n🌅 MORNING LIGHT — LIVE PILOT v0.4"
    )

    print(
        f"Run Time: "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    print(
        "Mode: Freshness Guard + "
        "Live WR5 + Live PSY12/24"
    )

    print(
        "Indicator Timeframe: 5-minute bars"
    )

    snapshots = []

    for ticker in WATCH_LIST:
        snapshot = fetch_live_snapshot(
            ticker
        )

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

    psy12_count = sum(
        snapshot["psy"].get(12) is not None
        for snapshot in snapshots
    )

    psy24_count = sum(
        snapshot["psy"].get(24) is not None
        for snapshot in snapshots
    )

    print("-" * 70)
    print("🌅 LIVE INDICATOR SUMMARY")
    print(f"Stocks scanned  : {len(snapshots)}")
    print(f"WR5 calculated  : {wr_count}")
    print(f"PSY12 calculated: {psy12_count}")
    print(f"PSY24 calculated: {psy24_count}")

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
        "✅ Live WR5 + PSY12/24 "
        "Engine v0.4 completed."
    )


if __name__ == "__main__":
    main()