import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

INFILE = Path(
    "reports/amount/individual_risk_budget_v0_4_participation.csv"
)

OUT_TXT = Path(
    "reports/amount/individual_risk_budget_v0_5_failure_structure.txt"
)

OUT_CSV = Path(
    "reports/amount/individual_risk_budget_v0_5_failure_buckets.csv"
)

ev = pd.read_csv(
    INFILE,
    dtype={"Ticker": str}
)

ev["Ticker"] = ev["Ticker"].str.zfill(4)
ev["T_action"] = pd.to_datetime(ev["T_action"])

ev["Failure"] = ev["FWD10"] <= 0
ev["Winner"] = ev["FWD10"] > 0

ev = ev.sort_values(
    ["T_action", "Ticker"]
).reset_index(drop=True)

# ============================================================
# 1. CALENDAR-DATE BUCKETS
#
# Multiple A2 events on the same T_action date belong to one
# time bucket. No artificial ordering is imposed within date.
# ============================================================

bucket_rows = []

for date, g in ev.groupby("T_action"):

    n = len(g)
    failures = int(g["Failure"].sum())
    winners = int(g["Winner"].sum())

    bucket_rows.append({
        "T_action": date,
        "Events": n,
        "Failures": failures,
        "Winners": winners,
        "AllFail": failures == n,
        "AnyFail": failures >= 1,
        "MultiFail": failures >= 2,
        "Tickers": ",".join(sorted(g["Ticker"].tolist())),
        "FailureTickers": ",".join(
            sorted(g.loc[g["Failure"], "Ticker"].tolist())
        ),
    })

buckets = pd.DataFrame(bucket_rows).sort_values(
    "T_action"
).reset_index(drop=True)

OUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

buckets.to_csv(
    OUT_CSV,
    index=False
)

# ============================================================
# 2. FAILURE-BUCKET STREAKS
#
# A failure bucket = at least one A2 event on that date failed.
#
# This avoids inventing ordering among same-day events.
# ============================================================

failure_bucket_streaks = []
current = 0

for x in buckets["AnyFail"]:

    if x:
        current += 1
    else:
        if current:
            failure_bucket_streaks.append(current)
        current = 0

if current:
    failure_bucket_streaks.append(current)

# ============================================================
# 3. ALL-FAIL BUCKET STREAKS
#
# Stronger definition:
# every A2 initiated in that date bucket eventually had
# FWD10 <= 0.
# ============================================================

allfail_streaks = []
current = 0

for x in buckets["AllFail"]:

    if x:
        current += 1
    else:
        if current:
            allfail_streaks.append(current)
        current = 0

if current:
    allfail_streaks.append(current)

# ============================================================
# 4. ROLLING FAILURE CLUSTERS
#
# Count number of failed A2 episodes initiated inside rolling
# calendar windows.
#
# This is NOT concurrent open risk.
# It measures temporal clustering of failed decisions.
# ============================================================

windows = [10, 20, 40]
rolling_summary = []

dates = ev["T_action"]

for days in windows:

    counts = []

    for d in dates.drop_duplicates():

        start = d - pd.Timedelta(days=days)

        g = ev[
            (ev["T_action"] > start)
            & (ev["T_action"] <= d)
        ]

        counts.append(
            int(g["Failure"].sum())
        )

    rolling_summary.append({
        "WindowDays": days,
        "MaxFailures": max(counts) if counts else 0,
        "P95Failures": (
            np.percentile(counts, 95)
            if counts else np.nan
        ),
        "MedianFailures": (
            np.median(counts)
            if counts else np.nan
        ),
    })

rolling = pd.DataFrame(rolling_summary)


def report():

    print("=" * 122)
    print("INDIVIDUAL RISK BUDGET v0.5 — HISTORICAL FAILURE STRUCTURE")
    print("SOURCE: COMPLETE v0.4 A2 EPISODE SET")
    print("FAILURE = FWD10 <= 0%")
    print("NO RISK-BUDGET PARAMETER | NO RETURN OPTIMIZATION")
    print("=" * 122)

    # ========================================================
    # A. BASELINE
    # ========================================================

    print()
    print("A. HISTORICAL A2 BASELINE")
    print("=" * 122)

    print("A2 episodes =", len(ev))
    print("Calendar T_action buckets =", len(buckets))
    print("Winners =", int(ev["Winner"].sum()))
    print("Failures =", int(ev["Failure"].sum()))

    print(
        "Failure rate = "
        f"{ev['Failure'].mean()*100:.1f}%"
    )

    print()
    print("Failures by ticker:")

    by_ticker = (
        ev.groupby("Ticker")
        .agg(
            N=("Failure", "size"),
            Failures=("Failure", "sum"),
            FailureRate=("Failure", "mean")
        )
    )

    by_ticker["FailureRate"] *= 100

    print(
        by_ticker.to_string(
            formatters={
                "FailureRate":
                    lambda x: f"{x:.1f}%"
            }
        )
    )

    # ========================================================
    # B. SAME-DAY FAILURE CONCENTRATION
    # ========================================================

    print()
    print("B. SAME-DAY FAILURE CONCENTRATION")
    print("=" * 122)

    multi_event = buckets[
        buckets["Events"] >= 2
    ]

    print(
        "Multi-A2 T_action dates =",
        len(multi_event)
    )

    if len(multi_event):

        print(
            "Any failure = "
            f"{multi_event['AnyFail'].mean()*100:.1f}%"
        )

        print(
            "Two-or-more failures = "
            f"{multi_event['MultiFail'].mean()*100:.1f}%"
        )

        print(
            "All same-day A2 failed = "
            f"{multi_event['AllFail'].mean()*100:.1f}%"
        )

        print(
            "Max same-day failures =",
            int(multi_event["Failures"].max())
        )

    # ========================================================
    # C. FAILURE-BUCKET STREAKS
    # ========================================================

    print()
    print("C. CHRONOLOGICAL FAILURE-BUCKET STREAKS")
    print("=" * 122)

    print(
        "Failure bucket = at least one failed A2 "
        "on that T_action date."
    )

    if failure_bucket_streaks:

        print(
            "Number of failure streaks =",
            len(failure_bucket_streaks)
        )

        print(
            "Max streak =",
            max(failure_bucket_streaks)
        )

        print(
            "Median streak =",
            f"{np.median(failure_bucket_streaks):.1f}"
        )

        print(
            "95th percentile streak =",
            f"{np.percentile(failure_bucket_streaks,95):.1f}"
        )

        dist = pd.Series(
            failure_bucket_streaks
        ).value_counts().sort_index()

        print()
        print("Streak distribution:")
        print(dist.to_string())

    # ========================================================
    # D. ALL-FAIL STREAKS
    # ========================================================

    print()
    print("D. ALL-FAIL BUCKET STREAKS")
    print("=" * 122)

    print(
        "All-fail bucket = every A2 initiated "
        "on that date eventually failed."
    )

    if allfail_streaks:

        print(
            "Max all-fail streak =",
            max(allfail_streaks)
        )

        print(
            "95th percentile =",
            f"{np.percentile(allfail_streaks,95):.1f}"
        )

        dist = pd.Series(
            allfail_streaks
        ).value_counts().sort_index()

        print()
        print("All-fail streak distribution:")
        print(dist.to_string())

    # ========================================================
    # E. TEMPORAL FAILURE CLUSTERS
    # ========================================================

    print()
    print("E. ROLLING FAILURE CLUSTERS")
    print("=" * 122)

    print(
        rolling.to_string(
            index=False,
            formatters={
                "P95Failures":
                    lambda x: f"{x:.1f}",
                "MedianFailures":
                    lambda x: f"{x:.1f}",
            }
        )
    )

    # ========================================================
    # F. WORST FAILURE BUCKETS
    # ========================================================

    print()
    print("F. WORST SAME-DAY FAILURE BUCKETS")
    print("=" * 122)

    worst = buckets.sort_values(
        ["Failures", "Events"],
        ascending=[False, False]
    ).head(12)

    print(
        worst[
            [
                "T_action",
                "Events",
                "Failures",
                "Tickers",
                "FailureTickers"
            ]
        ].to_string(index=False)
    )

    # ========================================================
    # G. INTERPRETATION GUARDRAIL
    # ========================================================

    print()
    print("G. INTERPRETATION GUARDRAIL")
    print("=" * 122)

    print(
        "FWD10 <= 0 is an outcome label for this historical "
        "stress study; it is NOT a production exit rule."
    )

    print(
        "Same-day initiation is NOT identical to simultaneous "
        "open-risk failure."
    )

    print(
        "Rolling failure clusters measure temporal concentration, "
        "not portfolio drawdown."
    )

    print(
        "Risk Budget will be applied only AFTER the historical "
        "failure structure is measured."
    )

    print()
    print("=" * 122)
    print("INDIVIDUAL RISK BUDGET v0.5 COMPLETE")
    print(
        "QUESTION: HOW OFTEN DID A2 FAILURES ACTUALLY CLUSTER "
        "IN HISTORICAL TIME?"
    )
    print("=" * 122)


OUT_TXT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUT_TXT.open(
    "w",
    encoding="utf-8"
) as f:

    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT_TXT)
print(" ", OUT_CSV)
