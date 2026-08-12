import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

INFILE = Path(
    "reports/amount/amount_sizing_v0_3R_events.csv"
)

OUTFILE = Path(
    "reports/amount/individual_risk_budget_v0_2_evidence_quality.txt"
)

ev = pd.read_csv(INFILE, dtype={"Ticker": str})
ev["Ticker"] = ev["Ticker"].str.zfill(4)

# ============================================================
# IMPORTANT
#
# v0.3R contains three rows per A2 episode when multiple
# distance thresholds were hit.
#
# For this interview we need ONE ROW PER A2 EPISODE.
# Therefore deduplicate by Ticker + T_action.
# ============================================================

base = (
    ev.sort_values(["Ticker", "T_action", "Threshold"])
      .drop_duplicates(["Ticker", "T_action"])
      .copy()
)

base["T_action"] = pd.to_datetime(base["T_action"])

# ============================================================
# We do NOT invent a new technical indicator.
#
# HitLag is available in v0.3R, but it measures time from
# T_action to later price damage, so it is FUTURE information.
# It MUST NOT be used to size at T_action.
#
# Therefore this audit first checks what real-time A2-quality
# information is actually available in the frozen event file.
# ============================================================

future_columns = {
    "Threshold",
    "HitDate",
    "HitLag",
    "State",
    "Bias3DownSeen",
    "MTM3DownSeen",
    "DMDownSeen",
    "Post1D",
    "Post3D",
    "Post5D",
    "Final10D_from_Taction",
}

candidate_realtime = [
    c for c in base.columns
    if c not in future_columns
    and c not in {"Ticker", "T_action"}
]

def report():

    print("=" * 118)
    print("INDIVIDUAL RISK BUDGET v0.2 — A2 EVIDENCE QUALITY INTERVIEW")
    print("QUESTION: DOES THE FROZEN EVENT FILE CONTAIN A REAL-TIME")
    print("A2 QUALITY VARIABLE THAT CAN JUSTIFY DIFFERENT RISK BUDGETS?")
    print("=" * 118)

    print()
    print("A. UNIQUE A2 EPISODES")
    print("=" * 118)

    print("N =", len(base))

    print()
    print(
        base.groupby("Ticker")
        .size()
        .to_string()
    )

    print()
    print("B. AVAILABLE COLUMNS")
    print("=" * 118)

    for c in base.columns:
        tag = (
            "FUTURE / POST-T_ACTION"
            if c in future_columns
            else "KNOWN OR STRUCTURAL"
        )

        print(f"{c:28} | {tag}")

    print()
    print("C. REAL-TIME QUALITY CANDIDATES IN FROZEN FILE")
    print("=" * 118)

    if candidate_realtime:

        for c in candidate_realtime:
            print(c)

    else:
        print("NONE")

    print()
    print("D. LOOK-AHEAD GUARDRAIL")
    print("=" * 118)

    print("The following MUST NOT determine Risk Budget at T_action:")
    print("- future threshold hit")
    print("- HitLag")
    print("- later Evidence deterioration state")
    print("- Post1D / Post3D / Post5D")
    print("- Final10D outcome")
    print()
    print("These variables are useful for validation,")
    print("but they are not available when the sizing decision is made.")

    print()
    print("E. INTERVIEW DECISION")
    print("=" * 118)

    if candidate_realtime:

        print(
            "REAL-TIME CANDIDATES EXIST."
        )
        print(
            "They may proceed to an incremental-value interview."
        )

    else:

        print(
            "NO REAL-TIME A2 QUALITY VARIABLE IS STORED "
            "IN THE FROZEN v0.3R EVENT FILE."
        )

        print()
        print(
            "Therefore v0.2 does NOT invent one."
        )

        print(
            "Current evidence supports a COMMON BASE RISK BUDGET "
            "for A2, subject to downstream ceilings."
        )

        print(
            "If differentiated A2 budgets are desired, "
            "a new prospective real-time evidence feature "
            "must first be defined and validated."
        )

    print()
    print("=" * 118)
    print("INDIVIDUAL RISK BUDGET v0.2 COMPLETE")
    print("NO LOOK-AHEAD INFORMATION MAY EARN MORE CAPITAL.")
    print("=" * 118)


OUTFILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUTFILE.open(
    "w",
    encoding="utf-8"
) as f:

    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUTFILE)
