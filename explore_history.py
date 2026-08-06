from pathlib import Path
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ============================================================
# MORNING LIGHT — HISTORICAL EVIDENCE EXPLORER v0.1
# Evidence → Pattern → Resonance
# ============================================================

HISTORY_FILE = Path("data/historical_indicator_log.csv")
REPORT_FOLDER = Path("reports")

DEFAULT_TICKER = "2330.TW"
DEFAULT_BARS = 120
MIN_PATTERN_BARS = 12


def load_history() -> pd.DataFrame:
    """Load and validate historical Three-in-One evidence."""

    if not HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"Historical log not found: {HISTORY_FILE}\n"
            "Please run: python backfill_history.py"
        )

    data = pd.read_csv(
        HISTORY_FILE,
        encoding="utf-8-sig",
    )

    required_columns = {
        "ticker",
        "bar_start",
        "close",
        "wr5",
        "psy12",
        "psy24",
        "j",
        "alignment_score",
        "future_return_1",
        "future_return_3",
        "future_return_6",
        "future_return_12",
    }

    missing = required_columns.difference(data.columns)

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing))
        )

    data["bar_start"] = pd.to_datetime(
        data["bar_start"],
        errors="coerce",
    )

    numeric_columns = [
        "close",
        "wr5",
        "psy12",
        "psy24",
        "j",
        "alignment_score",
        "future_return_1",
        "future_return_3",
        "future_return_6",
        "future_return_12",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data.dropna(
        subset=[
            "ticker",
            "bar_start",
            "close",
            "wr5",
            "psy12",
            "j",
        ]
    )

    data = (
        data.sort_values(
            ["ticker", "bar_start"],
            kind="stable",
        )
        .drop_duplicates(
            subset=["ticker", "bar_start"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return data


def select_history(
    data: pd.DataFrame,
    ticker: str,
    bars: int,
) -> pd.DataFrame:
    """Select one ticker and the latest requested number of bars."""

    selected = data[
        data["ticker"] == ticker
    ].copy()

    if selected.empty:
        available = ", ".join(
            sorted(data["ticker"].unique())
        )

        raise ValueError(
            f"No historical rows found for {ticker}.\n"
            f"Available tickers: {available}"
        )

    selected = (
        selected.sort_values("bar_start")
        .tail(bars)
        .reset_index(drop=True)
    )

    return selected


def add_pattern_fields(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Add direction, normalized level and pattern-event fields."""

    result = data.copy()

    result["wr_change"] = result["wr5"].diff()
    result["psy_change"] = result["psy12"].diff()
    result["j_change"] = result["j"].diff()
    result["price_change_pct"] = (
        result["close"].pct_change() * 100
    )

    result["wr_up"] = result["wr_change"] > 0
    result["psy_up"] = result["psy_change"] > 0
    result["j_up"] = result["j_change"] > 0

    result["calculated_alignment"] = (
        result[
            ["wr_up", "psy_up", "j_up"]
        ]
        .sum(axis=1)
        .astype(int)
    )

    result["three_up"] = (
        result["calculated_alignment"] == 3
    )

    result["two_up"] = (
        result["calculated_alignment"] == 2
    )

    result["zero_up"] = (
        result["calculated_alignment"] == 0
    )

    # Convert W/R from [-100, 0] to [0, 100].
    result["wr_tide"] = (
        result["wr5"] + 100
    ).clip(0, 100)

    result["psy_tide"] = (
        result["psy12"]
    ).clip(0, 100)

    # J can exceed 0–100, so clip only for the visual tide panel.
    result["j_tide"] = (
        result["j"]
    ).clip(0, 100)

    return result


def print_inventory(data: pd.DataFrame) -> None:
    """Show available historical evidence by ticker."""

    inventory = (
        data.groupby("ticker")
        .agg(
            bars=("bar_start", "count"),
            first_bar=("bar_start", "min"),
            last_bar=("bar_start", "max"),
        )
        .reset_index()
    )

    print("\n📚 HISTORICAL INVENTORY")
    print("-" * 76)

    for row in inventory.itertuples():
        print(
            f"{row.ticker:<10} | "
            f"Bars: {row.bars:<4} | "
            f"From: {row.first_bar:%Y-%m-%d %H:%M} | "
            f"To: {row.last_bar:%Y-%m-%d %H:%M}"
        )


def print_latest_timeline(
    data: pd.DataFrame,
    ticker: str,
) -> None:
    """Print the latest 20 bars in compact form."""

    latest = data.tail(20)

    print(
        f"\n🌊 HISTORICAL THREE-IN-ONE — {ticker}"
    )
    print("-" * 94)

    print(
        f"{'Time':<17}"
        f"{'Close':>10}"
        f"{'WR5':>10}"
        f"{'PSY12':>11}"
        f"{'J':>11}"
        f"{'Align':>10}"
        f"{'F+3':>11}"
    )

    print("-" * 94)

    for row in latest.itertuples():
        future_3 = (
            "—"
            if pd.isna(row.future_return_3)
            else f"{row.future_return_3:+.2f}%"
        )

        print(
            f"{row.bar_start:%m-%d %H:%M}  "
            f"{row.close:>10.2f}"
            f"{row.wr5:>10.2f}"
            f"{row.psy12:>11.2f}"
            f"{row.j:>11.2f}"
            f"{row.calculated_alignment:>8}/3"
            f"{future_3:>11}"
        )


def create_chart(
    data: pd.DataFrame,
    ticker: str,
) -> Path:
    """Create the historical Pattern + Resonance Map."""

    REPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_ticker = ticker.replace(".", "_")

    output_file = (
        REPORT_FOLDER
        / f"historical_pattern_resonance_{safe_ticker}.png"
    )

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(15, 12),
        sharex=True,
        gridspec_kw={
            "height_ratios": [2.0, 2.1, 1.0, 1.2]
        },
        constrained_layout=True,
    )

    times = data["bar_start"]

    # --------------------------------------------------------
    # Panel 1 — Price and resonance-event markers
    # --------------------------------------------------------
    axes[0].plot(
        times,
        data["close"],
        linewidth=1.7,
        label="Close",
    )

    three_up = data[data["three_up"]]
    zero_up = data[data["zero_up"]]

    axes[0].scatter(
        three_up["bar_start"],
        three_up["close"],
        marker="^",
        s=55,
        label="3/3 upward resonance",
        zorder=5,
    )

    axes[0].scatter(
        zero_up["bar_start"],
        zero_up["close"],
        marker="v",
        s=35,
        label="0/3 upward alignment",
        zorder=5,
    )

    axes[0].set_title(
        f"Morning Light Historical Pattern + Resonance — {ticker}"
    )
    axes[0].set_ylabel("Price")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="best")

    # --------------------------------------------------------
    # Panel 2 — Three-in-One tide
    # --------------------------------------------------------
    axes[1].plot(
        times,
        data["wr_tide"],
        linewidth=1.5,
        label="W/R5 transformed",
    )

    axes[1].plot(
        times,
        data["psy_tide"],
        linewidth=1.5,
        label="PSY12",
    )

    axes[1].plot(
        times,
        data["j_tide"],
        linewidth=1.5,
        label="J clipped for view",
    )

    axes[1].axhline(
        20,
        linestyle="--",
        linewidth=1,
        label="Low zone 20",
    )

    axes[1].axhline(
        80,
        linestyle="--",
        linewidth=1,
        label="High zone 80",
    )

    axes[1].set_ylim(-5, 105)
    axes[1].set_ylabel("Three-in-One Tide")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(
        loc="upper left",
        ncol=5,
        fontsize=8,
    )

    # --------------------------------------------------------
    # Panel 3 — Resonance score
    # --------------------------------------------------------
    axes[2].step(
        times,
        data["calculated_alignment"],
        where="mid",
        linewidth=1.4,
        label="Upward alignment",
    )

    axes[2].fill_between(
        times,
        0,
        data["calculated_alignment"],
        step="mid",
        alpha=0.25,
    )

    axes[2].set_ylim(-0.1, 3.3)
    axes[2].set_yticks([0, 1, 2, 3])
    axes[2].set_ylabel("Resonance")
    axes[2].grid(True, axis="y", alpha=0.25)
    axes[2].legend(loc="upper left")

    # --------------------------------------------------------
    # Panel 4 — Future returns already prepared by Backfill
    # --------------------------------------------------------
    axes[3].plot(
        times,
        data["future_return_1"],
        linewidth=1.0,
        label="+1 bar",
    )

    axes[3].plot(
        times,
        data["future_return_3"],
        linewidth=1.0,
        label="+3 bars",
    )

    axes[3].plot(
        times,
        data["future_return_6"],
        linewidth=1.0,
        label="+6 bars",
    )

    axes[3].axhline(
        0,
        linestyle="--",
        linewidth=1,
    )

    axes[3].set_ylabel("Future Return %")
    axes[3].set_xlabel("5-minute bar start")
    axes[3].grid(True, alpha=0.25)
    axes[3].legend(
        loc="upper left",
        ncol=3,
    )

    locator = mdates.AutoDateLocator(
        minticks=6,
        maxticks=14,
    )

    formatter = mdates.ConciseDateFormatter(
        locator
    )

    axes[3].xaxis.set_major_locator(locator)
    axes[3].xaxis.set_major_formatter(formatter)

    fig.savefig(
        output_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_file


def summarize_resonance(
    data: pd.DataFrame,
) -> None:
    """Provide a first descriptive summary, not a trading conclusion."""

    summary = (
        data.groupby("calculated_alignment")
        .agg(
            observations=("bar_start", "count"),
            average_future_1=(
                "future_return_1",
                "mean",
            ),
            average_future_3=(
                "future_return_3",
                "mean",
            ),
            average_future_6=(
                "future_return_6",
                "mean",
            ),
        )
        .reindex([0, 1, 2, 3])
    )

    print("\n📊 FIRST RESONANCE SUMMARY")
    print("-" * 80)

    print(
        f"{'Align':<10}"
        f"{'N':>8}"
        f"{'Avg +1':>14}"
        f"{'Avg +3':>14}"
        f"{'Avg +6':>14}"
    )

    print("-" * 80)

    for alignment, row in summary.iterrows():
        observations = (
            0
            if pd.isna(row["observations"])
            else int(row["observations"])
        )

        def format_return(value: float) -> str:
            if pd.isna(value):
                return "—"
            return f"{value:+.3f}%"

        print(
            f"{alignment}/3"
            f"{observations:>15}"
            f"{format_return(row['average_future_1']):>14}"
            f"{format_return(row['average_future_3']):>14}"
            f"{format_return(row['average_future_6']):>14}"
        )


def main() -> None:
    """Explore historical Pattern + Resonance evidence."""

    ticker = (
        sys.argv[1].upper()
        if len(sys.argv) > 1
        else DEFAULT_TICKER
    )

    try:
        requested_bars = (
            int(sys.argv[2])
            if len(sys.argv) > 2
            else DEFAULT_BARS
        )
    except ValueError as error:
        raise ValueError(
            "Bars must be an integer, "
            "for example: python explore_history.py 2330.TW 120"
        ) from error

    if requested_bars <= 0:
        raise ValueError(
            "Bars must be greater than zero."
        )

    print(
        "\n🌅 MORNING LIGHT — "
        "HISTORICAL EVIDENCE EXPLORER v0.1"
    )

    history = load_history()

    print(f"Historical log : {HISTORY_FILE}")
    print(f"Total rows     : {len(history)}")
    print(f"Selected ticker: {ticker}")
    print(f"Requested bars : {requested_bars}")

    print_inventory(history)

    selected = select_history(
        history,
        ticker,
        requested_bars,
    )

    selected = add_pattern_fields(selected)

    print_latest_timeline(
        selected,
        ticker,
    )

    summarize_resonance(selected)

    chart_file = create_chart(
        selected,
        ticker,
    )

    print("\n" + "-" * 76)
    print(f"Bars analyzed : {len(selected)}")
    print(f"Chart created : {chart_file}")

    if len(selected) < MIN_PATTERN_BARS:
        print(
            "⚠️ Pattern status: "
            "Too few bars for meaningful observation."
        )
    else:
        print(
            "✅ Historical Pattern + Resonance Map "
            "created successfully."
        )

    print(
        "Interpretation : Descriptive evidence only; "
        "not yet a validated probability."
    )
    
    print(
        "Safety         : Research use only — "
        "not for execution"
    )


if __name__ == "__main__":
    main()