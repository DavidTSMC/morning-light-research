from pathlib import Path
import pandas as pd

from research.daily_report.weekly_clinical_context import (
    build_watch_map,
)

SOURCE = Path("reports/daily_report/clinical_map_latest.csv")
CANDIDATE = Path(
    "reports/daily_report/clinical_map_weekly_candidate.csv"
)

WEEKLY_COLS = [
    "W Trend",
    "W Pulse",
    "W Loc",
    "Resonance",
]

EXPECTED_TICKERS = [
    "2059", "2330", "2382", "2454", "2603", "2882",
    "3017", "3583", "3661", "3665", "6472",
]

ALLOWED = {
    "W Trend": {"↑多", "→轉", "↓弱"},
    "W Pulse": {"擴", "縮", "修", "弱"},
    "W Loc": {"低", "中", "高", "極"},
    "Resonance": {"◎齊", "○同", "△轉", "△錯", "×衝"},
}


def fail(message: str):
    raise RuntimeError(f"BRIDGE BLOCKED: {message}")


def main():
    print("MORNING LIGHT — WEEKLY CLINICAL BRIDGE v0.1")
    print("CANDIDATE EXPORT ONLY | PRODUCTION NOT TOUCHED")
    print("=" * 78)

    if not SOURCE.exists():
        fail(f"source not found: {SOURCE}")

    # Read ticker as string so identity is preserved exactly.
    source = pd.read_csv(
        SOURCE,
        dtype={"股票": str},
    )

    required = ["股票"] + WEEKLY_COLS
    missing = [c for c in required if c not in source.columns]
    if missing:
        fail(f"missing columns: {missing}")

    if len(source) != 11:
        fail(f"expected 11 rows, got {len(source)}")

    tickers = source["股票"].astype(str).str.strip().tolist()

    if tickers != EXPECTED_TICKERS:
        fail(
            "ticker identity/order mismatch\n"
            f"expected={EXPECTED_TICKERS}\n"
            f"actual={tickers}"
        )

    # Frozen Weekly Clinical Context.
    weekly_rows = build_watch_map()

    if len(weekly_rows) != 11:
        fail(
            f"weekly context expected 11 rows, "
            f"got {len(weekly_rows)}"
        )

    weekly_map = {
        str(r["ticker"]).strip(): r
        for r in weekly_rows
    }

    if set(weekly_map) != set(EXPECTED_TICKERS):
        fail("weekly context ticker set mismatch")

    # Preserve an untouched in-memory reference.
    before = source.copy(deep=True)
    candidate = source.copy(deep=True)

    # Replace ONLY the four approved Weekly fields.
    for idx, ticker in enumerate(tickers):
        w = weekly_map[ticker]

        candidate.at[idx, "W Trend"] = w["W Trend"]
        candidate.at[idx, "W Pulse"] = w["W Pulse"]
        candidate.at[idx, "W Loc"] = w["W Loc"]
        candidate.at[idx, "Resonance"] = w["Resonance"]

    # -------------------------------------------------
    # CUSTOMS GATE 1 — vocabularies / completeness
    # -------------------------------------------------
    for col in WEEKLY_COLS:
        values = candidate[col].astype(str).str.strip()

        if values.isin(["", "—", "-", "nan", "None"]).any():
            fail(f"{col} contains blank/unresolved values")

        bad = sorted(set(values) - ALLOWED[col])
        if bad:
            fail(f"{col} invalid labels: {bad}")

    # -------------------------------------------------
    # CUSTOMS GATE 2 — all non-weekly columns unchanged
    # -------------------------------------------------
    non_weekly_cols = [
        c for c in source.columns
        if c not in WEEKLY_COLS
    ]

    before_nonweekly = before[non_weekly_cols].reset_index(drop=True)
    after_nonweekly = candidate[non_weekly_cols].reset_index(drop=True)

    if not before_nonweekly.equals(after_nonweekly):
        diff_cols = [
            c for c in non_weekly_cols
            if not before_nonweekly[c].equals(after_nonweekly[c])
        ]
        fail(
            "non-weekly evidence changed: "
            + ", ".join(diff_cols)
        )

    # -------------------------------------------------
    # CUSTOMS GATE 3 — ticker/date discipline
    # -------------------------------------------------
    for r in weekly_rows:
        if r["weekly_asof"] > r["daily_asof"]:
            fail(
                f"{r['ticker']} weekly date "
                f"{r['weekly_asof']} > daily date "
                f"{r['daily_asof']}"
            )

    weekly_dates = sorted({
        r["weekly_asof"]
        for r in weekly_rows
    })

    # -------------------------------------------------
    # EXPORT CANDIDATE ONLY
    # -------------------------------------------------
    candidate.to_csv(
        CANDIDATE,
        index=False,
        encoding="utf-8-sig",
    )

    # Read-back validation: prove exported artifact is usable.
    check = pd.read_csv(
        CANDIDATE,
        dtype={"股票": str},
    )

    if len(check) != len(candidate):
        fail("candidate read-back row count mismatch")

    if list(check.columns) != list(candidate.columns):
        fail("candidate read-back schema mismatch")

    print("WEEKLY CLINICAL BRIDGE AUDIT")
    print("-" * 78)
    print("Rows                       11/11 PASS")
    print("Ticker identity/order      PASS")
    print("Non-weekly columns         UNCHANGED PASS")
    print("W Trend                    11/11 PASS")
    print("W Pulse                    11/11 PASS")
    print("W Loc                      11/11 PASS")
    print("Resonance                  11/11 PASS")
    print("Completed-week discipline  PASS")
    print("Candidate read-back        PASS")

    print()
    print("Weekly completed as-of:", ", ".join(weekly_dates))

    print()
    print("CHANGED COLUMNS ALLOWED:")
    for c in WEEKLY_COLS:
        print(" -", c)

    print()
    print(
        candidate[
            ["股票", "W Trend", "W Pulse", "W Loc", "Resonance"]
        ].to_string(index=False)
    )

    print()
    print("Candidate:", CANDIDATE)
    print("SOURCE UNCHANGED")
    print("PRODUCTION NOT TOUCHED")
    print("NO EMAIL / NO MAIN.PY CHANGE")


if __name__ == "__main__":
    main()
