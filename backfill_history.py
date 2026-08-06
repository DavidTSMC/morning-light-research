from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
import sys

# ============================================================
# MORNING LIGHT — HISTORICAL BACKFILL v0.1
# First validation target: 2330.TW
# ============================================================

TICKER = sys.argv[1].upper() if len(sys.argv) > 1 else "2330.TW"
PERIOD = "5d"
INTERVAL = "5m"

OUTPUT_FOLDER = Path("data")
OUTPUT_FILE = OUTPUT_FOLDER / "historical_indicator_log.csv"
LIVE_LOG_FILE = OUTPUT_FOLDER / "live_indicator_log.csv"

WR_PERIOD = 5
PSY_PERIODS = (12, 24)

KDJ_N = 9
KDJ_SMOOTH_K = 3
KDJ_SMOOTH_D = 3

TAIWAN_OPEN = "09:00"
TAIWAN_CLOSE = "13:30"


def flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Convert possible yfinance MultiIndex columns to simple names."""

    result = data.copy()

    if isinstance(result.columns, pd.MultiIndex):
        # For a single ticker, keep the price-field level.
        result.columns = [
            column[0] if isinstance(column, tuple) else column
            for column in result.columns
        ]

    result.columns = [
        str(column).strip().title()
        for column in result.columns
    ]

    return result


def prepare_time_index(data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timestamps to Asia/Taipei and keep Taiwan regular session.

    Yahoo 5-minute timestamps are treated as bar-start times.
    """

    result = data.copy()

    index = pd.DatetimeIndex(result.index)

    if index.tz is None:
        index = index.tz_localize(
            "Asia/Taipei",
            ambiguous="infer",
            nonexistent="shift_forward",
        )
    else:
        index = index.tz_convert("Asia/Taipei")

    result.index = index
    result.index.name = "bar_start"

    result = result.between_time(
        TAIWAN_OPEN,
        TAIWAN_CLOSE,
        inclusive="both",
    )

    return result


def calculate_wr(
    data: pd.DataFrame,
    period: int,
) -> pd.Series:
    """
    Williams %R:
    (Highest High - Close) / (Highest High - Lowest Low) × -100
    """

    highest_high = data["High"].rolling(
        period,
        min_periods=period,
    ).max()

    lowest_low = data["Low"].rolling(
        period,
        min_periods=period,
    ).min()

    denominator = highest_high - lowest_low

    wr = (
        (highest_high - data["Close"])
        / denominator.replace(0, np.nan)
        * -100
    )

    # When the entire range is zero, use 0 rather than infinity.
    wr = wr.where(denominator != 0, 0.0)

    return wr


def calculate_psy(
    close: pd.Series,
    period: int,
) -> pd.Series:
    """
    Psychological Line:
    Number of rising closes in the latest N bars / N × 100

    A rising close means:
    current close > previous close.
    """

    rising = (
        close.diff() > 0
    ).astype(float)

    psy = (
        rising.rolling(
            period,
            min_periods=period,
        ).sum()
        / period
        * 100
    )

    return psy


def chinese_sma(
    source: pd.Series,
    period: int,
    weight: int = 1,
    initial_value: float = 50.0,
) -> pd.Series:
    """
    Taiwan/Chinese-style recursive SMA:

    SMA_t =
        [weight × X_t
         + (period - weight) × SMA_(t-1)]
        / period

    For KDJ(9,3,3), period=3 and weight=1.
    """

    values: list[float] = []
    previous = initial_value

    for value in source:
        if pd.isna(value):
            values.append(np.nan)
            continue

        current = (
            weight * float(value)
            + (period - weight) * previous
        ) / period

        values.append(current)
        previous = current

    return pd.Series(
        values,
        index=source.index,
        dtype=float,
    )


def calculate_kdj(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    KDJ parameters: 9, 3, 3

    RSV = (Close - Lowest Low 9)
          / (Highest High 9 - Lowest Low 9) × 100

    K = recursive SMA(RSV, 3, 1)
    D = recursive SMA(K, 3, 1)
    J = 3K - 2D
    """

    lowest_low = data["Low"].rolling(
        KDJ_N,
        min_periods=KDJ_N,
    ).min()

    highest_high = data["High"].rolling(
        KDJ_N,
        min_periods=KDJ_N,
    ).max()

    denominator = highest_high - lowest_low

    rsv = (
        (data["Close"] - lowest_low)
        / denominator.replace(0, np.nan)
        * 100
    )

    rsv = rsv.where(
        denominator != 0,
        50.0,
    )

    k = chinese_sma(
        rsv,
        period=KDJ_SMOOTH_K,
        weight=1,
        initial_value=50.0,
    )

    d = chinese_sma(
        k,
        period=KDJ_SMOOTH_D,
        weight=1,
        initial_value=50.0,
    )

    j = 3 * k - 2 * d

    return pd.DataFrame(
        {
            "k": k,
            "d": d,
            "j": j,
        },
        index=data.index,
    )


def direction_text(change: float) -> str | None:
    """Convert one-bar change to UP, DOWN or FLAT."""

    if pd.isna(change):
        return None

    if change > 0:
        return "UP"

    if change < 0:
        return "DOWN"

    return "FLAT"


def download_history() -> pd.DataFrame:
    """Download recent 5-minute OHLCV history."""

    print(f"Downloading      : {TICKER}")
    print(f"Period / interval: {PERIOD} / {INTERVAL}")

    data = yf.download(
        tickers=TICKER,
        period=PERIOD,
        interval=INTERVAL,
        auto_adjust=False,
        prepost=False,
        progress=False,
        threads=False,
    )

    if data.empty:
        raise RuntimeError(
            "Yahoo returned no historical data."
        )

    data = flatten_columns(data)
    data = prepare_time_index(data)

    required = {
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    }

    missing = required.difference(data.columns)

    if missing:
        raise ValueError(
            "Missing OHLCV columns: "
            + ", ".join(sorted(missing))
        )

    data = data[
        ["Open", "High", "Low", "Close", "Volume"]
    ].copy()

    data = data.dropna(
        subset=["Open", "High", "Low", "Close"]
    )

    data = data[
        ~data.index.duplicated(keep="last")
    ].sort_index()

    return data


def build_indicator_history(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate Three-in-One indicators for every 5-minute bar."""

    result = data.copy()

    result["wr5"] = calculate_wr(
        result,
        WR_PERIOD,
    )

    result["psy12"] = calculate_psy(
        result["Close"],
        12,
    )

    result["psy24"] = calculate_psy(
        result["Close"],
        24,
    )

    kdj = calculate_kdj(result)

    result["k"] = kdj["k"]
    result["d"] = kdj["d"]
    result["j"] = kdj["j"]

    result["wr5_previous"] = result["wr5"].shift(1)
    result["psy12_previous"] = result["psy12"].shift(1)
    result["psy24_previous"] = result["psy24"].shift(1)
    result["j_previous"] = result["j"].shift(1)

    result["wr_change"] = result["wr5"].diff()
    result["psy12_change"] = result["psy12"].diff()
    result["psy24_change"] = result["psy24"].diff()
    result["j_change"] = result["j"].diff()

    result["wr_direction"] = result[
        "wr_change"
    ].map(direction_text)

    result["psy12_direction"] = result[
        "psy12_change"
    ].map(direction_text)

    result["psy24_direction"] = result[
        "psy24_change"
    ].map(direction_text)

    result["j_direction"] = result[
        "j_change"
    ].map(direction_text)

    result["wr_up"] = result["wr_change"] > 0
    result["psy12_up"] = result["psy12_change"] > 0
    result["j_up"] = result["j_change"] > 0

    result["alignment_score"] = (
        result[
            ["wr_up", "psy12_up", "j_up"]
        ]
        .sum(axis=1)
        .astype("Int64")
    )

    result["alignment"] = (
        result["alignment_score"]
        .astype("string")
        + "/3"
    )

    # Future price movements reserved for first backtest.
    for bars_ahead in (1, 3, 6, 12):
        result[f"future_return_{bars_ahead}"] = (
            result["Close"].shift(-bars_ahead)
            / result["Close"]
            - 1
        ) * 100

    return result


def format_for_storage(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Create a clean historical evidence table."""

    output = data.reset_index().copy()

    output["bar_start"] = pd.to_datetime(
        output["bar_start"]
    ).dt.strftime("%Y-%m-%d %H:%M")

    output["broker_bar_end"] = (
        pd.to_datetime(output["bar_start"])
        + pd.Timedelta(minutes=5)
    ).dt.strftime("%Y-%m-%d %H:%M")

    output.insert(
        0,
        "computed_at",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    output.insert(1, "source", "historical_backfill")
    output.insert(2, "ticker", TICKER)

    output = output.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume_shares",
        }
    )

    ordered_columns = [
        "computed_at",
        "source",
        "ticker",
        "bar_start",
        "broker_bar_end",
        "open",
        "high",
        "low",
        "close",
        "volume_shares",
        "wr5",
        "psy12",
        "psy24",
        "k",
        "d",
        "j",
        "wr5_previous",
        "psy12_previous",
        "psy24_previous",
        "j_previous",
        "wr_change",
        "psy12_change",
        "psy24_change",
        "j_change",
        "wr_direction",
        "psy12_direction",
        "psy24_direction",
        "j_direction",
        "alignment_score",
        "alignment",
        "future_return_1",
        "future_return_3",
        "future_return_6",
        "future_return_12",
    ]

    return output[ordered_columns]


def merge_and_save(
    new_data: pd.DataFrame,
) -> tuple[int, int]:
    """Save historical data without duplicate ticker/bar pairs."""

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT_FILE.exists():
        try:
            old_data = pd.read_csv(
                OUTPUT_FILE,
                encoding="utf-8-sig",
            )
        except pd.errors.EmptyDataError:
            old_data = pd.DataFrame()
    else:
        old_data = pd.DataFrame()

    rows_before = len(old_data)

    if old_data.empty:
        combined = new_data.copy()
    else:
        combined = pd.concat(
            [old_data, new_data],
            ignore_index=True,
        )

    combined = combined.drop_duplicates(
        subset=["ticker", "bar_start"],
        keep="last",
    )

    combined = combined.sort_values(
        ["ticker", "bar_start"],
        kind="stable",
    ).reset_index(drop=True)

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    return rows_before, len(combined)


def print_recent_evidence(
    data: pd.DataFrame,
) -> None:
    """Print the latest 12 valid Three-in-One rows."""

    valid = data.dropna(
        subset=["wr5", "psy12", "j"]
    ).tail(12)

    print("\n🌊 LATEST HISTORICAL EVIDENCE")
    print("-" * 90)

    print(
        f"{'Time':<18}"
        f"{'Close':>10}"
        f"{'WR5':>10}"
        f"{'PSY12':>12}"
        f"{'J':>12}"
        f"{'Align':>10}"
    )

    print("-" * 90)

    for row in valid.itertuples():
        print(
            f"{row.bar_start:<18}"
            f"{row.close:>10.2f}"
            f"{row.wr5:>10.2f}"
            f"{row.psy12:>12.2f}"
            f"{row.j:>12.2f}"
            f"{row.alignment:>10}"
        )


def compare_with_live(
    historical: pd.DataFrame,
) -> None:
    """
    Compare overlapping historical and live rows.

    This does not change either data file.
    """

    if not LIVE_LOG_FILE.exists():
        print(
            "\nLive comparison : "
            "live log not found — skipped"
        )
        return

    live = pd.read_csv(
        LIVE_LOG_FILE,
        encoding="utf-8-sig",
    )

    live = live[
        live["ticker"] == TICKER
    ].copy()

    if live.empty:
        print(
            "\nLive comparison : "
            f"no {TICKER} row — skipped"
        )
        return

    comparison = live.merge(
        historical[
            [
                "ticker",
                "bar_start",
                "wr5",
                "psy12",
                "psy24",
                "k",
                "d",
                "j",
            ]
        ],
        on=["ticker", "bar_start"],
        how="inner",
        suffixes=("_live", "_history"),
    )

    if comparison.empty:
        print(
            "\nLive comparison : "
            "no overlapping bar yet"
        )
        return

    latest = comparison.iloc[-1]

    print("\n🔬 LIVE vs HISTORICAL FORMULA CHECK")
    print("-" * 64)
    print(f"Ticker / bar : {latest['ticker']} | {latest['bar_start']}")

    for field in (
        "wr5",
        "psy12",
        "psy24",
        "k",
        "d",
        "j",
    ):
        live_value = latest[f"{field}_live"]
        history_value = latest[f"{field}_history"]

        difference = (
            float(history_value)
            - float(live_value)
        )

        print(
            f"{field.upper():<8}"
            f"Live: {float(live_value):>9.2f} | "
            f"History: {float(history_value):>9.2f} | "
            f"Diff: {difference:>8.2f}"
        )


def main() -> None:
    """Download, calculate, store and validate historical evidence."""

    print(
        "\n🌅 MORNING LIGHT — "
        "HISTORICAL BACKFILL v0.1"
    )

    print(
        f"Run Time         : "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    raw = download_history()

    print(f"Downloaded bars  : {len(raw)}")
    print(
        f"First bar        : "
        f"{raw.index.min():%Y-%m-%d %H:%M}"
    )
    print(
        f"Last bar         : "
        f"{raw.index.max():%Y-%m-%d %H:%M}"
    )

    calculated = build_indicator_history(raw)
    historical = format_for_storage(calculated)

    # Keep rows once all three core values are available.
    historical = historical.dropna(
        subset=["wr5", "psy12", "j"]
    ).reset_index(drop=True)

    rows_before, rows_after = merge_and_save(
        historical
    )

    net_added = rows_after - rows_before

    print_recent_evidence(historical)

    print("\n" + "-" * 72)
    print(f"Valid backfill rows : {len(historical)}")
    print(f"Rows before         : {rows_before}")
    print(f"Rows after          : {rows_after}")
    print(f"Net new rows        : {net_added}")
    print(f"Historical log      : {OUTPUT_FILE}")
    print(
        "Duplicate rule      : "
        "ticker + bar_start, keep latest"
    )

    compare_with_live(historical)

    print("\n✅ Historical Backfill v0.1 completed.")
    print(
        "Safety              : "
        "Research use only — not for execution"
    )


if __name__ == "__main__":
    main()