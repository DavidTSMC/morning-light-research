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

KDJ_PERIOD = 9
KDJ_SMOOTHING = 3


def flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns for one ticker."""

    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.get_level_values(0)

    return data


def fetch_previous_close(ticker: str) -> float | None:
    """Fetch the most recent completed daily close."""

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

    return float(daily.iloc[-2]["Close"])


def calculate_quote_age(latest_time: pd.Timestamp) -> float:
    """Calculate quote age in minutes."""

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


def get_direction(
    current_value: float,
    previous_value: float,
    tolerance: float = 0.01,
) -> str:
    """Return direction arrow."""

    change = current_value - previous_value

    if change > tolerance:
        return "↑"

    if change < -tolerance:
        return "↓"

    return "→"


# ============================================================
# WR ENGINE
# ============================================================

def calculate_wr(
    data: pd.DataFrame,
    period: int = WR_PERIOD,
) -> pd.Series:
    """Calculate Williams %R."""

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

    return wr.where(price_range != 0)


def classify_wr(
    current_wr: float,
    previous_wr: float,
) -> dict:
    """Interpret WR5 movement."""

    change = current_wr - previous_wr
    direction = get_direction(
        current_wr,
        previous_wr,
    )

    crossed_trigger = (
        previous_wr <= WR_TRIGGER_LEVEL
        and current_wr > WR_TRIGGER_LEVEL
    )

    if crossed_trigger:
        status = "🟢 TRIGGERED"
        explanation = "WR5 crossed above -80"

    elif current_wr <= WR_TRIGGER_LEVEL and change > 0:
        status = "🟡 RECOVERING"
        explanation = "Oversold zone is improving"

    elif current_wr <= WR_TRIGGER_LEVEL:
        status = "🔴 OVERSOLD"
        explanation = "WR5 remains below -80"

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
        "distance": distance,
        "crossed_trigger": crossed_trigger,
    }


def build_wr_snapshot(
    intraday: pd.DataFrame,
) -> dict | None:
    """Build the latest WR5 observation."""

    wr_series = calculate_wr(
        intraday,
        period=WR_PERIOD,
    ).dropna()

    if len(wr_series) < 2:
        return None

    return classify_wr(
        current_wr=float(wr_series.iloc[-1]),
        previous_wr=float(wr_series.iloc[-2]),
    )


# ============================================================
# PSY ENGINE
# ============================================================

def calculate_psy(
    close: pd.Series,
    period: int,
) -> pd.Series:
    """Calculate Psychological Line."""

    rising = (
        close.diff() > 0
    ).astype(float)

    return (
        rising.rolling(
            window=period,
            min_periods=period,
        ).sum()
        / period
        * 100
    )


def build_one_psy_snapshot(
    close: pd.Series,
    period: int,
) -> dict | None:
    """Build one PSY-period observation."""

    if len(close) < period + 1:
        return None

    psy_series = calculate_psy(
        close,
        period,
    ).dropna()

    if len(psy_series) < 2:
        return None

    previous_value = float(
        psy_series.iloc[-2]
    )

    current_value = float(
        psy_series.iloc[-1]
    )

    direction = get_direction(
        current_value,
        previous_value,
    )

    rising_count = int(
        round(current_value * period / 100)
    )

    if current_value <= 25:
        status = (
            "🟡 LOW — RECOVERING"
            if direction == "↑"
            else "🔴 LOW"
        )

    elif current_value >= 75:
        status = (
            "🟡 HIGH — COOLING"
            if direction == "↓"
            else "🔴 HIGH"
        )

    else:
        status = "⚪ NEUTRAL"

    return {
        "period": period,
        "previous": previous_value,
        "current": current_value,
        "change": current_value - previous_value,
        "direction": direction,
        "rising_count": rising_count,
        "status": status,
    }


def build_psy_snapshot(
    intraday: pd.DataFrame,
) -> dict:
    """Build PSY12 and PSY24 observations."""

    close = intraday["Close"].dropna()

    return {
        period: build_one_psy_snapshot(
            close,
            period,
        )
        for period in PSY_PERIODS
    }


# ============================================================
# J / KDJ ENGINE
# ============================================================

def calculate_kdj(
    data: pd.DataFrame,
    period: int = KDJ_PERIOD,
    smoothing: int = KDJ_SMOOTHING,
) -> pd.DataFrame:
    """
    Calculate standard KDJ.

    RSV = (Close - Lowest Low)
          / (Highest High - Lowest Low) × 100

    K = previous K × 2/3 + RSV × 1/3
    D = previous D × 2/3 + K × 1/3
    J = 3K - 2D

    Initial K and D are set to 50.
    """

    lowest_low = data["Low"].rolling(
        window=period,
        min_periods=period,
    ).min()

    highest_high = data["High"].rolling(
        window=period,
        min_periods=period,
    ).max()

    price_range = highest_high - lowest_low

    rsv = (
        (data["Close"] - lowest_low)
        / price_range
        * 100
    )

    rsv = rsv.where(price_range != 0)
    rsv = rsv.fillna(50.0)

    alpha = 1 / smoothing

    k = rsv.ewm(
        alpha=alpha,
        adjust=False,
    ).mean()

    d = k.ewm(
        alpha=alpha,
        adjust=False,
    ).mean()

    j = 3 * k - 2 * d

    return pd.DataFrame(
        {
            "K": k,
            "D": d,
            "J": j,
        },
        index=data.index,
    )


def classify_j(
    current_j: float,
    previous_j: float,
) -> dict:
    """Interpret the latest J movement."""

    change = current_j - previous_j

    direction = get_direction(
        current_j,
        previous_j,
    )

    v_turn = (
        current_j > previous_j
    )

    crossed_zero = (
        previous_j <= 0
        and current_j > 0
    )

    crossed_30 = (
        previous_j <= 30
        and current_j > 30
    )

    if crossed_zero:
        status = "🟢 EXTREME V-TURN"
        explanation = "J crossed upward through 0"

    elif crossed_30:
        status = "🟢 RECOVERY TRIGGER"
        explanation = "J crossed upward through 30"

    elif current_j < 0 and v_turn:
        status = "🟡 EXTREME — RECOVERING"
        explanation = "J remains below 0 but is turning upward"

    elif current_j < 0:
        status = "🔴 EXTREME LOW"
        explanation = "J remains below 0"

    elif current_j <= 30 and v_turn:
        status = "🟡 LOW — RECOVERING"
        explanation = "J is below 30 and turning upward"

    elif current_j <= 30:
        status = "🟠 LOW"
        explanation = "J remains in the low zone"

    elif current_j >= 100:
        status = "🔴 EXTREME HIGH"
        explanation = "J is above 100"

    else:
        status = "⚪ NEUTRAL"
        explanation = "J is in the middle range"

    return {
        "previous": previous_j,
        "current": current_j,
        "change": change,
        "direction": direction,
        "status": status,
        "explanation": explanation,
        "v_turn": v_turn,
        "crossed_zero": crossed_zero,
        "crossed_30": crossed_30,
    }


def build_j_snapshot(
    intraday: pd.DataFrame,
) -> dict | None:
    """Build latest K, D and J observations."""

    kdj = calculate_kdj(
        intraday,
        period=KDJ_PERIOD,
        smoothing=KDJ_SMOOTHING,
    ).dropna()

    if len(kdj) < 2:
        return None

    previous_row = kdj.iloc[-2]
    current_row = kdj.iloc[-1]

    result = classify_j(
        current_j=float(current_row["J"]),
        previous_j=float(previous_row["J"]),
    )

    result["k"] = float(current_row["K"])
    result["d"] = float(current_row["D"])

    return result


# ============================================================
# THREE-IN-ONE
# ============================================================

def build_three_in_one(
    wr_snapshot: dict | None,
    psy_snapshot: dict,
    j_snapshot: dict | None,
) -> dict:
    """Build preliminary WR + PSY + J interaction status."""

    wr_up = bool(
        wr_snapshot
        and wr_snapshot["direction"] == "↑"
    )

    psy12 = psy_snapshot.get(12)

    psy_up = bool(
        psy12
        and psy12["direction"] == "↑"
    )

    j_up = bool(
        j_snapshot
        and j_snapshot["direction"] == "↑"
    )

    score = sum(
        [
            wr_up,
            psy_up,
            j_up,
        ]
    )

    if score == 3:
        status = "🟢 THREE-IN-ONE RESONANCE"

    elif score == 2:
        status = "🟡 TWO OF THREE ALIGNED"

    elif score == 1:
        status = "⚪ EARLY / ISOLATED MOVEMENT"

    else:
        status = "🔴 NO UPWARD ALIGNMENT"

    return {
        "wr_up": wr_up,
        "psy_up": psy_up,
        "j_up": j_up,
        "score": score,
        "status": status,
    }


# ============================================================
# LIVE SNAPSHOT
# ============================================================

def empty_snapshot(
    ticker: str,
    status: str,
    freshness: str,
    safety_notice: str,
) -> dict:
    """Return a consistent empty snapshot."""

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
        "j": None,
        "three_in_one": None,
    }


def fetch_live_snapshot(
    ticker: str,
) -> dict:
    """Fetch near-live data with WR, PSY and J."""

    try:
        # Five days provide enough warm-up history for K and D.
        intraday = yf.download(
            ticker,
            period="5d",
            interval="5m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if intraday.empty:
            return empty_snapshot(
                ticker,
                "NO DATA",
                "🔴 UNKNOWN",
                "No usable market data",
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
                "No valid intraday prices"
            )

        latest_price = float(
            intraday.iloc[-1]["Close"]
        )

        previous_close = fetch_previous_close(
            ticker
        )

        change = None
        change_pct = None

        if previous_close not in (None, 0):
            change = (
                latest_price - previous_close
            )

            change_pct = (
                change / previous_close * 100
            )

        latest_time = pd.Timestamp(
            intraday.index[-1]
        )

        # Sum volume only for the latest trading date.
        latest_date = latest_time.date()

        same_day = intraday[
            intraday.index.date == latest_date
        ]

        volume_shares = int(
            same_day["Volume"].fillna(0).sum()
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

        j_snapshot = build_j_snapshot(
            intraday
        )

        three_in_one = build_three_in_one(
            wr_snapshot,
            psy_snapshot,
            j_snapshot,
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
            "volume_lots": volume_shares / 1000,
            "quote_age": quote_age,
            "freshness": freshness,
            "safety_notice": safety_notice,
            "wr": wr_snapshot,
            "psy": psy_snapshot,
            "j": j_snapshot,
            "three_in_one": three_in_one,
        }

    except Exception as error:
        return empty_snapshot(
            ticker,
            f"ERROR: {error}",
            "🔴 ERROR",
            "Snapshot could not be validated",
        )


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def print_wr(
    snapshot: dict | None,
) -> None:
    """Print WR5."""

    print("\n📡 INDICATOR 1 — W/R")

    if snapshot is None:
        print("WR5             : NOT AVAILABLE")
        return

    print(
        f"WR5 Previous    : "
        f"{snapshot['previous']:.2f}"
    )

    print(
        f"WR5 Current     : "
        f"{snapshot['current']:.2f} "
        f"{snapshot['direction']}"
    )

    print(
        f"WR5 Status      : "
        f"{snapshot['status']}"
    )


def print_psy(
    snapshots: dict,
) -> None:
    """Print PSY12 and PSY24."""

    print("\n🧠 INDICATOR 2 — PSY")

    for period in PSY_PERIODS:
        snapshot = snapshots.get(period)

        if snapshot is None:
            print(
                f"PSY{period:<11}: NOT AVAILABLE"
            )
            continue

        print(
            f"PSY{period} Previous  : "
            f"{snapshot['previous']:.2f}"
        )

        print(
            f"PSY{period} Current   : "
            f"{snapshot['current']:.2f} "
            f"{snapshot['direction']}"
        )

        print(
            f"PSY{period} Rising    : "
            f"{snapshot['rising_count']}/{period}"
        )

        print(
            f"PSY{period} Status    : "
            f"{snapshot['status']}"
        )


def print_j(
    snapshot: dict | None,
) -> None:
    """Print J and supporting K/D values."""

    print("\n⚡ INDICATOR 3 — J")

    if snapshot is None:
        print("J               : NOT AVAILABLE")
        return

    print("KDJ Parameters  : 9, 3, 3")

    print(
        f"K Current       : "
        f"{snapshot['k']:.2f}"
    )

    print(
        f"D Current       : "
        f"{snapshot['d']:.2f}"
    )

    print(
        f"J Previous      : "
        f"{snapshot['previous']:.2f}"
    )

    print(
        f"J Current       : "
        f"{snapshot['current']:.2f} "
        f"{snapshot['direction']}"
    )

    print(
        f"J Change        : "
        f"{snapshot['change']:+.2f}"
    )

    print(
        f"J Status        : "
        f"{snapshot['status']}"
    )

    print(
        f"J Explanation   : "
        f"{snapshot['explanation']}"
    )


def print_three_in_one(
    snapshot: dict | None,
) -> None:
    """Print preliminary three-in-one interaction."""

    print("\n🌅 THREE-IN-ONE — W/R + PSY12 + J")

    if snapshot is None:
        print("Status          : NOT AVAILABLE")
        return

    print(
        f"W/R Up          : "
        f"{'YES' if snapshot['wr_up'] else 'NO'}"
    )

    print(
        f"PSY12 Up        : "
        f"{'YES' if snapshot['psy_up'] else 'NO'}"
    )

    print(
        f"J Up            : "
        f"{'YES' if snapshot['j_up'] else 'NO'}"
    )

    print(
        f"Alignment       : "
        f"{snapshot['score']}/3"
    )

    print(
        f"Status          : "
        f"{snapshot['status']}"
    )


def print_snapshot(
    snapshot: dict,
) -> None:
    """Print one complete stock snapshot."""

    print("-" * 72)
    print(f"Ticker          : {snapshot['ticker']}")
    print(f"Status          : {snapshot['status']}")
    print(f"Latest Time     : {snapshot['time']}")

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
        marker = (
            "🟢"
            if snapshot["change_pct"] >= 0
            else "🔴"
        )

        print(
            f"Daily Change    : {marker} "
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
    print_j(snapshot["j"])
    print_three_in_one(
        snapshot["three_in_one"]
    )


def main() -> None:
    """Run Morning Light Live v0.5."""

    print(
        "\n🌅 MORNING LIGHT — LIVE PILOT v0.5"
    )

    print(
        f"Run Time: "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    print(
        "Mode: Live W/R + PSY + J "
        "Three-in-One Candidate"
    )

    print(
        "Timeframe: 5-minute bars"
    )

    snapshots = []

    for ticker in WATCH_LIST:
        snapshot = fetch_live_snapshot(
            ticker
        )

        snapshots.append(snapshot)
        print_snapshot(snapshot)

    available_count = sum(
        snapshot["three_in_one"] is not None
        for snapshot in snapshots
    )

    full_alignment_count = sum(
        bool(
            snapshot["three_in_one"]
            and snapshot["three_in_one"]["score"] == 3
        )
        for snapshot in snapshots
    )

    print("-" * 72)
    print("🌅 LIVE THREE-IN-ONE SUMMARY")
    print(f"Stocks scanned  : {len(snapshots)}")
    print(f"Results built   : {available_count}")
    print(f"Full alignment  : {full_alignment_count}")
    print(
        "Validation      : J still requires "
        "broker Reality Check"
    )
    print(
        "Safety          : Research use only — "
        "not for execution"
    )
    print(
        "✅ Live W/R + PSY + J "
        "Engine v0.5 completed."
    )


if __name__ == "__main__":
    main()