from datetime import datetime
from pathlib import Path

import pandas as pd

from run_live import WATCH_LIST, fetch_live_snapshot


LOG_FOLDER = Path("data")
LOG_FILE = LOG_FOLDER / "live_indicator_log.csv"

BAR_MINUTES = 5


def safe_get(
    source: dict | None,
    key: str,
):
    """Safely read one value from an optional dictionary."""

    if not source:
        return None

    return source.get(key)


def build_log_row(
    snapshot: dict,
) -> dict | None:
    """Convert one live snapshot into one CSV row."""

    if (
        snapshot.get("status") != "OK"
        or snapshot.get("time") in (None, "-")
    ):
        return None

    bar_start = pd.Timestamp(
        snapshot["time"]
    )

    broker_bar_end = (
        bar_start
        + pd.Timedelta(minutes=BAR_MINUTES)
    )

    wr = snapshot.get("wr")
    psy = snapshot.get("psy", {})
    psy12 = psy.get(12)
    psy24 = psy.get(24)
    j_snapshot = snapshot.get("j")
    three_in_one = snapshot.get("three_in_one")

    alignment_score = safe_get(
        three_in_one,
        "score",
    )

    alignment_text = (
        f"{alignment_score}/3"
        if alignment_score is not None
        else None
    )

    return {
        # Identification
        "run_time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "ticker": snapshot.get("ticker"),
        "bar_start": bar_start.strftime(
            "%Y-%m-%d %H:%M"
        ),
        "broker_bar_end": broker_bar_end.strftime(
            "%Y-%m-%d %H:%M"
        ),

        # Price and volume
        "close": snapshot.get("price"),
        "previous_close": snapshot.get(
            "previous_close"
        ),
        "daily_change": snapshot.get("change"),
        "daily_change_pct": snapshot.get(
            "change_pct"
        ),
        "volume_shares": snapshot.get(
            "volume_shares"
        ),
        "volume_lots": snapshot.get(
            "volume_lots"
        ),

        # Three-in-One raw values
        "wr5": safe_get(wr, "current"),
        "psy12": safe_get(psy12, "current"),
        "psy24": safe_get(psy24, "current"),
        "k": safe_get(j_snapshot, "k"),
        "d": safe_get(j_snapshot, "d"),
        "j": safe_get(j_snapshot, "current"),

        # Previous values
        "wr5_previous": safe_get(
            wr,
            "previous",
        ),
        "psy12_previous": safe_get(
            psy12,
            "previous",
        ),
        "psy24_previous": safe_get(
            psy24,
            "previous",
        ),
        "j_previous": safe_get(
            j_snapshot,
            "previous",
        ),

        # Direction and interaction
        "wr_direction": safe_get(
            wr,
            "direction",
        ),
        "psy12_direction": safe_get(
            psy12,
            "direction",
        ),
        "psy24_direction": safe_get(
            psy24,
            "direction",
        ),
        "j_direction": safe_get(
            j_snapshot,
            "direction",
        ),
        "alignment_score": alignment_score,
        "alignment": alignment_text,
        "three_in_one_status": safe_get(
            three_in_one,
            "status",
        ),

        # Indicator status
        "wr_status": safe_get(wr, "status"),
        "psy12_status": safe_get(
            psy12,
            "status",
        ),
        "psy24_status": safe_get(
            psy24,
            "status",
        ),
        "j_status": safe_get(
            j_snapshot,
            "status",
        ),

        # Data quality
        "freshness": snapshot.get("freshness"),
        "quote_age_minutes": snapshot.get(
            "quote_age"
        ),
        "safety_notice": snapshot.get(
            "safety_notice"
        ),

        # Expandable fields — reserved for later
        "bias3": None,
        "mtm3": None,
        "di_osc": None,
        "d_minus_m": None,
    }


def load_existing_log() -> pd.DataFrame:
    """Load existing CSV or return an empty table."""

    if not LOG_FILE.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            LOG_FILE,
            encoding="utf-8-sig",
        )

    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def save_rows(
    new_rows: list[dict],
) -> tuple[int, int]:
    """
    Save rows and remove duplicate ticker/bar pairs.

    Returns:
        rows_before, rows_after
    """

    LOG_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    old_data = load_existing_log()
    new_data = pd.DataFrame(new_rows)

    rows_before = len(old_data)

    if old_data.empty:
        combined = new_data
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
        by=["bar_start", "ticker"],
        kind="stable",
    ).reset_index(drop=True)

    combined.to_csv(
        LOG_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    return rows_before, len(combined)


def main() -> None:
    """Collect and save the latest bar for every ticker."""

    print(
        "\n🌅 MORNING LIGHT — "
        "THREE-IN-ONE LOGGER v0.1"
    )

    print(
        f"Run Time        : "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    )

    rows = []

    for ticker in WATCH_LIST:
        print(f"Collecting      : {ticker}")

        snapshot = fetch_live_snapshot(
            ticker
        )

        row = build_log_row(snapshot)

        if row is None:
            print(
                f"Skipped         : {ticker} "
                f"({snapshot.get('status')})"
            )
            continue

        rows.append(row)

        print(
            f"Captured        : {ticker} | "
            f"{row['bar_start']} | "
            f"Alignment {row['alignment']}"
        )

    if not rows:
        print(
            "\n⚠️ No valid rows were available."
        )
        return

    rows_before, rows_after = save_rows(
        rows
    )

    net_added = rows_after - rows_before

    print("-" * 68)
    print(f"Valid snapshots : {len(rows)}")
    print(f"Rows before     : {rows_before}")
    print(f"Rows after      : {rows_after}")
    print(f"Net new rows    : {net_added}")
    print(f"Log file        : {LOG_FILE}")
    print(
        "Duplicate rule  : "
        "ticker + bar_start, keep latest"
    )
    print(
        "✅ Three-in-One evidence "
        "saved successfully."
    )


if __name__ == "__main__":
    main()