from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


LOG_FILE = Path("data/live_indicator_log.csv")
REPORT_FOLDER = Path("reports")

DEFAULT_TICKER = "2330.TW"
MIN_PATTERN_BARS = 3


def load_log() -> pd.DataFrame:
    """Load and validate the persistent Three-in-One log."""

    if not LOG_FILE.exists():
        raise FileNotFoundError(
            f"Log file not found: {LOG_FILE}\n"
            "Please run: python save_live_log.py"
        )

    data = pd.read_csv(
        LOG_FILE,
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
        "freshness",
    }

    missing = required_columns.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing))
        )

    data["bar_start"] = pd.to_datetime(
        data["bar_start"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["ticker", "bar_start"]
    )

    data = data.sort_values(
        ["ticker", "bar_start"],
        kind="stable",
    ).reset_index(drop=True)

    return data


def show_inventory(data: pd.DataFrame) -> None:
    """Print how many bars are available for each ticker."""

    inventory = (
        data.groupby("ticker")
        .agg(
            bars=("bar_start", "count"),
            first_bar=("bar_start", "min"),
            last_bar=("bar_start", "max"),
        )
        .reset_index()
    )

    print("\n📚 LOG INVENTORY")
    print("-" * 72)

    for row in inventory.itertuples():
        print(
            f"{row.ticker:<10} | "
            f"Bars: {row.bars:<4} | "
            f"From: {row.first_bar:%Y-%m-%d %H:%M} | "
            f"To: {row.last_bar:%Y-%m-%d %H:%M}"
        )


def select_ticker(
    data: pd.DataFrame,
    ticker: str,
) -> pd.DataFrame:
    """Return one ticker's timeline."""

    selected = data[
        data["ticker"] == ticker
    ].copy()

    if selected.empty:
        available = ", ".join(
            sorted(data["ticker"].unique())
        )

        raise ValueError(
            f"No rows found for {ticker}.\n"
            f"Available tickers: {available}"
        )

    selected = (
        selected.sort_values("bar_start")
        .drop_duplicates(
            subset=["bar_start"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return selected


def add_pattern_fields(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate direction, velocity and resonance fields."""

    result = data.copy()

    numeric_columns = [
        "close",
        "wr5",
        "psy12",
        "psy24",
        "j",
        "alignment_score",
    ]

    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["wr_velocity"] = (
        result["wr5"].diff()
    )

    result["psy_velocity"] = (
        result["psy12"].diff()
    )

    result["j_velocity"] = (
        result["j"].diff()
    )

    result["price_return_pct"] = (
        result["close"].pct_change() * 100
    )

    result["wr_up"] = (
        result["wr_velocity"] > 0
    )

    result["psy_up"] = (
        result["psy_velocity"] > 0
    )

    result["j_up"] = (
        result["j_velocity"] > 0
    )

    result["calculated_alignment"] = (
        result[
            ["wr_up", "psy_up", "j_up"]
        ]
        .sum(axis=1)
        .astype("Int64")
    )

    return result


def direction_symbol(value: float) -> str:
    """Convert a numeric change into an arrow."""

    if pd.isna(value):
        return "·"

    if value > 0:
        return "↑"

    if value < 0:
        return "↓"

    return "→"


def print_timeline(
    data: pd.DataFrame,
    ticker: str,
) -> None:
    """Print a compact Three-in-One evidence timeline."""

    print(
        f"\n🌊 THREE-IN-ONE TIMELINE — {ticker}"
    )
    print("-" * 92)

    header = (
        f"{'Time':<17}"
        f"{'Close':>10}"
        f"{'WR5':>10}"
        f"{'PSY12':>12}"
        f"{'J':>12}"
        f"{'Resonance':>14}"
        f"{'Freshness':>13}"
    )

    print(header)
    print("-" * 92)

    for row in data.itertuples():
        time_text = row.bar_start.strftime(
            "%m-%d %H:%M"
        )

        wr_text = (
            f"{row.wr5:.2f}"
            f"{direction_symbol(row.wr_velocity)}"
        )

        psy_text = (
            f"{row.psy12:.2f}"
            f"{direction_symbol(row.psy_velocity)}"
        )

        j_text = (
            f"{row.j:.2f}"
            f"{direction_symbol(row.j_velocity)}"
        )

        resonance = (
            "—"
            if pd.isna(row.calculated_alignment)
            else f"{int(row.calculated_alignment)}/3"
        )

        print(
            f"{time_text:<17}"
            f"{row.close:>10.2f}"
            f"{wr_text:>10}"
            f"{psy_text:>12}"
            f"{j_text:>12}"
            f"{resonance:>14}"
            f"{str(row.freshness):>13}"
        )


def normalize_series(
    series: pd.Series,
) -> pd.Series:
    """
    Normalize a series to 0–100.

    This is used only for visual comparison.
    Original values remain unchanged in the log.
    """

    clean = pd.to_numeric(
        series,
        errors="coerce",
    )

    minimum = clean.min()
    maximum = clean.max()

    if (
        pd.isna(minimum)
        or pd.isna(maximum)
        or maximum == minimum
    ):
        return pd.Series(
            50.0,
            index=series.index,
        )

    return (
        (clean - minimum)
        / (maximum - minimum)
        * 100
    )


def create_resonance_chart(
    data: pd.DataFrame,
    ticker: str,
) -> Path:
    """Create the first Morning Light Pattern/Resonance chart."""

    REPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_ticker = ticker.replace(".", "_")

    output_file = (
        REPORT_FOLDER
        / f"three_in_one_resonance_{safe_ticker}.png"
    )

    chart_data = data.copy()

    chart_data["wr_normalized"] = (
        normalize_series(chart_data["wr5"])
    )

    chart_data["psy_normalized"] = (
        normalize_series(chart_data["psy12"])
    )

    chart_data["j_normalized"] = (
        normalize_series(chart_data["j"])
    )

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(12, 10),
        sharex=True,
        constrained_layout=True,
    )

    # Panel 1 — Price
    axes[0].plot(
        chart_data["bar_start"],
        chart_data["close"],
        marker="o",
        linewidth=2,
        label="Close",
    )

    axes[0].set_title(
        f"Morning Light Three-in-One Evidence — {ticker}"
    )
    axes[0].set_ylabel("Price")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Panel 2 — Normalized indicator tide
    axes[1].plot(
        chart_data["bar_start"],
        chart_data["wr_normalized"],
        marker="o",
        label="W/R5 normalized",
    )

    axes[1].plot(
        chart_data["bar_start"],
        chart_data["psy_normalized"],
        marker="o",
        label="PSY12 normalized",
    )

    axes[1].plot(
        chart_data["bar_start"],
        chart_data["j_normalized"],
        marker="o",
        label="J normalized",
    )

    axes[1].axhline(
        50,
        linestyle="--",
        linewidth=1,
    )

    axes[1].set_ylim(-5, 105)
    axes[1].set_ylabel("Normalized Tide")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    # Panel 3 — Resonance score
    resonance = (
        chart_data["calculated_alignment"]
        .fillna(0)
        .astype(float)
    )

    axes[2].bar(
        chart_data["bar_start"],
        resonance,
        width=0.0025,
        label="Upward alignment",
    )

    axes[2].set_ylim(0, 3.3)
    axes[2].set_yticks([0, 1, 2, 3])
    axes[2].set_ylabel("Resonance")
    axes[2].set_xlabel("5-minute bar start")
    axes[2].grid(True, axis="y", alpha=0.3)
    axes[2].legend()

    fig.autofmt_xdate()

    fig.savefig(
        output_file,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    return output_file


def main() -> None:
    """Read the log and explore Pattern + Resonance."""

    ticker = (
        sys.argv[1].upper()
        if len(sys.argv) > 1
        else DEFAULT_TICKER
    )

    print(
        "\n🌅 MORNING LIGHT — "
        "EVIDENCE EXPLORER v0.1"
    )

    data = load_log()

    print(f"Log file       : {LOG_FILE}")
    print(f"Total rows     : {len(data)}")
    print(f"Selected ticker: {ticker}")

    show_inventory(data)

    selected = select_ticker(
        data,
        ticker,
    )

    selected = add_pattern_fields(
        selected
    )

    print_timeline(
        selected,
        ticker,
    )

    chart_file = create_resonance_chart(
        selected,
        ticker,
    )

    print("\n" + "-" * 72)
    print(f"Bars analyzed  : {len(selected)}")
    print(f"Chart created  : {chart_file}")

    if len(selected) < MIN_PATTERN_BARS:
        print(
            "⚠️ Pattern status: "
            "Not enough sequential bars yet."
        )
        print(
            "   At least 3 bars are required "
            "to begin observing direction."
        )
    else:
        print(
            "✅ Pattern and resonance timeline "
            "created successfully."
        )

    print(
        "Safety          : "
        "Research use only — not for execution"
    )


if __name__ == "__main__":
    main()