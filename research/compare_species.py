"""
=========================================================
 MORNING LIGHT RESEARCH
 Compare Species v0.2

 Evidence first.
 Never fit the data.
 Let the data teach us.
 Compare before concluding.
 Confidence is earned, not assumed.

 Mission:
 Compare Three-in-One pattern frequency and subsequent
 outcomes across different market species.

 Research only.
 No trading decisions.
=========================================================
"""

from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT_FOLDER = Path(__file__).resolve().parents[1]

HISTORY_FILE = (
    ROOT_FOLDER
    / "data"
    / "historical_indicator_log.csv"
)

REPORT_FOLDER = ROOT_FOLDER / "reports"

COUNTS_FILE = (
    REPORT_FOLDER
    / "species_alignment_counts.csv"
)

OUTCOMES_FILE = (
    REPORT_FOLDER
    / "species_alignment_outcomes.csv"
)

THREE_OF_THREE_FILE = (
    REPORT_FOLDER
    / "species_3of3_summary.csv"
)


# ============================================================
# MARKET SPECIES
# ============================================================

SPECIES_MAP = {
    "0050.TW": "ETF Benchmark",
    "2330.TW": "Mega Cap Semiconductor",
    "2454.TW": "IC Design",
    "2882.TW": "Financial",
    "8291.TWO": "Stress Test / Thin Liquidity",
    # Backfill v0.1 currently retains only Taiwan-hours data.
    "GC=F": "Gold / Asia-session Slice",
}

HORIZONS = (1, 3, 6, 12)


# ============================================================
# LOAD AND VALIDATE
# ============================================================

def load_history() -> pd.DataFrame:
    """Load and validate the historical evidence library."""

    if not HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"Historical evidence not found:\n"
            f"{HISTORY_FILE}\n\n"
            "Run backfill_history.py first."
        )

    data = pd.read_csv(
        HISTORY_FILE,
        encoding="utf-8-sig",
    )

    required_columns = {
        "ticker",
        "bar_start",
        "alignment_score",
        "future_return_1",
        "future_return_3",
        "future_return_6",
        "future_return_12",
    }

    missing_columns = (
        required_columns.difference(data.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    data["bar_start"] = pd.to_datetime(
        data["bar_start"],
        errors="coerce",
    )

    numeric_columns = [
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
            "alignment_score",
        ]
    ).copy()

    data["alignment_score"] = (
        data["alignment_score"].astype(int)
    )

    data = data[
        data["alignment_score"].between(0, 3)
    ].copy()

    data["species"] = (
        data["ticker"]
        .map(SPECIES_MAP)
        .fillna("Unclassified")
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


# ============================================================
# SUMMARY CALCULATIONS
# ============================================================

def positive_rate(values: pd.Series) -> float:
    """Return the percentage of valid returns above zero."""

    valid = values.dropna()

    if valid.empty:
        return float("nan")

    return float(
        (valid > 0).mean() * 100
    )


def build_inventory(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Build ticker/species evidence inventory."""

    return (
        data.groupby(
            ["ticker", "species"],
            as_index=False,
        )
        .agg(
            bars=("bar_start", "count"),
            first_bar=("bar_start", "min"),
            last_bar=("bar_start", "max"),
        )
        .sort_values("ticker")
        .reset_index(drop=True)
    )


def build_alignment_counts(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Count 0/3, 1/3, 2/3 and 3/3 bars."""

    counts = (
        data.groupby(
            [
                "ticker",
                "species",
                "alignment_score",
            ]
        )
        .size()
        .unstack(fill_value=0)
        .reindex(
            columns=[0, 1, 2, 3],
            fill_value=0,
        )
    )

    counts.columns = [
        "align_0_of_3",
        "align_1_of_3",
        "align_2_of_3",
        "align_3_of_3",
    ]

    return (
        counts.reset_index()
        .sort_values("ticker")
        .reset_index(drop=True)
    )


def build_outcome_summary(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize subsequent returns by ticker, species
    and alignment level.
    """

    aggregations = {
        "observations": (
            "bar_start",
            "count",
        ),
    }

    for horizon in HORIZONS:
        return_column = (
            f"future_return_{horizon}"
        )

        aggregations[
            f"avg_future_{horizon}"
        ] = (
            return_column,
            "mean",
        )

        aggregations[
            f"median_future_{horizon}"
        ] = (
            return_column,
            "median",
        )

        aggregations[
            f"positive_rate_{horizon}"
        ] = (
            return_column,
            positive_rate,
        )

    summary = (
        data.groupby(
            [
                "ticker",
                "species",
                "alignment_score",
            ],
            as_index=False,
        )
        .agg(**aggregations)
        .sort_values(
            ["ticker", "alignment_score"]
        )
        .reset_index(drop=True)
    )

    return summary


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def format_return(value: float) -> str:
    """Format a return percentage."""

    if pd.isna(value):
        return "—"

    return f"{value:+.3f}%"


def format_rate(value: float) -> str:
    """Format a positive-return rate."""

    if pd.isna(value):
        return "—"

    return f"{value:.1f}%"


def print_inventory(
    inventory: pd.DataFrame,
) -> None:
    """Print the current Market Species Library."""

    print("\n🌍 MARKET SPECIES INVENTORY")
    print("-" * 92)

    for row in inventory.itertuples():
        print(
            f"{row.ticker:<10} | "
            f"{row.species:<32} | "
            f"Bars: {row.bars:<4} | "
            f"{row.first_bar:%Y-%m-%d %H:%M}"
            f" → "
            f"{row.last_bar:%Y-%m-%d %H:%M}"
        )


def print_alignment_counts(
    counts: pd.DataFrame,
) -> None:
    """Print pattern-frequency comparison."""

    print("\n🧭 ALIGNMENT FREQUENCY")
    print("-" * 92)

    print(
        f"{'Ticker':<11}"
        f"{'Species':<32}"
        f"{'0/3':>8}"
        f"{'1/3':>8}"
        f"{'2/3':>8}"
        f"{'3/3':>8}"
    )

    print("-" * 92)

    for row in counts.itertuples():
        print(
            f"{row.ticker:<11}"
            f"{row.species:<32}"
            f"{row.align_0_of_3:>8}"
            f"{row.align_1_of_3:>8}"
            f"{row.align_2_of_3:>8}"
            f"{row.align_3_of_3:>8}"
        )


def print_three_of_three(
    outcomes: pd.DataFrame,
) -> None:
    """Print descriptive outcomes after 3/3 bars."""

    three_of_three = outcomes[
        outcomes["alignment_score"] == 3
    ].copy()

    print("\n🌅 3/3 ALIGNMENT — FIRST CROSS-SPECIES VIEW")
    print("-" * 92)

    if three_of_three.empty:
        print("No 3/3 observations are available.")
        return

    for row in three_of_three.itertuples():
        print(
            f"\n{row.ticker} | {row.species}"
        )

        print(
            f"3/3 bar observations : "
            f"{row.observations}"
        )

        for horizon in HORIZONS:
            average = getattr(
                row,
                f"avg_future_{horizon}",
            )

            positive = getattr(
                row,
                f"positive_rate_{horizon}",
            )

            print(
                f"  +{horizon:<2} bars | "
                f"Average: {format_return(average):>9} | "
                f"Positive: {format_rate(positive):>7}"
            )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the first Compare Species experiment."""

    print(
        "\n🌅 MORNING LIGHT RESEARCH"
    )

    print(
        "Compare Species v0.2"
    )

    print(
        "Evidence → Pattern → Species → Outcome"
    )

    history = load_history()

    inventory = build_inventory(history)

    alignment_counts = (
        build_alignment_counts(history)
    )

    outcomes = build_outcome_summary(
        history
    )

    three_of_three = outcomes[
        outcomes["alignment_score"] == 3
    ].copy()

    REPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    alignment_counts.to_csv(
        COUNTS_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    outcomes.to_csv(
        OUTCOMES_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    three_of_three.to_csv(
        THREE_OF_THREE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"\nHistorical rows : {len(history)}"
    )

    print(
        f"Tickers          : "
        f"{history['ticker'].nunique()}"
    )

    print_inventory(inventory)

    print_alignment_counts(
        alignment_counts
    )

    print_three_of_three(outcomes)

    print("\n" + "-" * 92)

    print(
        f"Counts report    : {COUNTS_FILE}"
    )

    print(
        f"Outcome report   : {OUTCOMES_FILE}"
    )

    print(
        f"3/3 report       : {THREE_OF_THREE_FILE}"
    )

    print(
        "\nInterpretation   : "
        "Descriptive bar-level evidence only."
    )

    print(
        "Important        : "
        "Consecutive bars may belong to the same "
        "market episode."
    )

    print(
        "Gold context     : "
        "GC=F currently represents the "
        "09:00–13:30 Asia/Taipei session slice."
    )

    print(
        "Decision status  : "
        "No probability conclusion yet."
    )

    print(
        "\n✅ Compare Species v0.2 completed."
    )


if __name__ == "__main__":
    main()
    