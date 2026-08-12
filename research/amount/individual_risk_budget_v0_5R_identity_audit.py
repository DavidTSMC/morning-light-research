import pandas as pd
from pathlib import Path
from contextlib import redirect_stdout

INFILE = Path(
    "reports/amount/individual_risk_budget_v0_4_participation.csv"
)

OUT_TXT = Path(
    "reports/amount/individual_risk_budget_v0_5R_identity_audit.txt"
)

OUT_CSV = Path(
    "reports/amount/individual_risk_budget_v0_5R_unique_episodes.csv"
)

ev = pd.read_csv(
    INFILE,
    dtype={"Ticker": str}
)

ev["Ticker"] = ev["Ticker"].str.zfill(4)
ev["T_action"] = pd.to_datetime(ev["T_action"])

KEY = ["Ticker", "T_action"]

# ============================================================
# A. IDENTITY MULTIPLICITY
# ============================================================

identity = (
    ev.groupby(KEY, as_index=False)
      .agg(
          RawRows=("FWD10", "size"),
          FWD10_min=("FWD10", "min"),
          FWD10_max=("FWD10", "max"),
          FWD10_first=("FWD10", "first"),
      )
)

identity["OutcomeSpread"] = (
    identity["FWD10_max"]
    - identity["FWD10_min"]
)

identity["DuplicateIdentity"] = (
    identity["RawRows"] > 1
)

# ============================================================
# B. CONSISTENCY AUDIT
#
# Same Ticker + same T_action should have same FWD10.
# If not, STOP: identity collapse is not yet safe.
# ============================================================

inconsistent = identity[
    identity["OutcomeSpread"].abs() > 1e-12
].copy()

# ============================================================
# C. UNIQUE ECONOMIC DECISIONS
#
# Only safe if duplicate rows have identical outcome.
# ============================================================

unique = (
    ev.sort_values(KEY)
      .drop_duplicates(KEY, keep="first")
      .copy()
)

unique["Failure"] = unique["FWD10"] <= 0
unique["Winner"] = unique["FWD10"] > 0

mult_map = identity[
    KEY + ["RawRows"]
]

unique = unique.merge(
    mult_map,
    on=KEY,
    how="left"
)

unique = unique.sort_values(
    ["T_action", "Ticker"]
).reset_index(drop=True)


def report():

    print("=" * 120)
    print("INDIVIDUAL RISK BUDGET v0.5R — EPISODE IDENTITY AUDIT")
    print("ONE ECONOMIC DECISION -> ONE CAPITAL PERMISSION")
    print("IDENTITY KEY = TICKER + T_ACTION")
    print("=" * 120)

    print()
    print("A. RAW vs UNIQUE")
    print("=" * 120)

    print("Raw rows =", len(ev))
    print("Unique Ticker + T_action =", len(identity))
    print(
        "Duplicate excess rows =",
        len(ev) - len(identity)
    )
    print(
        "Identities with >1 raw row =",
        int(identity["DuplicateIdentity"].sum())
    )

    print()
    print("Multiplicity distribution:")
    print(
        identity["RawRows"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("B. MOST DUPLICATED IDENTITIES")
    print("=" * 120)

    dup = identity[
        identity["RawRows"] > 1
    ].sort_values(
        ["RawRows", "T_action", "Ticker"],
        ascending=[False, True, True]
    )

    if len(dup):
        print(
            dup[
                [
                    "Ticker",
                    "T_action",
                    "RawRows",
                    "FWD10_min",
                    "FWD10_max",
                    "OutcomeSpread",
                ]
            ].head(30).to_string(index=False)
        )
    else:
        print("NONE")

    print()
    print("C. OUTCOME CONSISTENCY")
    print("=" * 120)

    print(
        "Duplicate identities with inconsistent FWD10 =",
        len(inconsistent)
    )

    if len(inconsistent):

        print()
        print("WARNING: DO NOT COLLAPSE YET.")
        print(
            inconsistent[
                [
                    "Ticker",
                    "T_action",
                    "RawRows",
                    "FWD10_min",
                    "FWD10_max",
                    "OutcomeSpread",
                ]
            ].to_string(index=False)
        )

    else:

        print(
            "PASS: duplicate detections carry identical "
            "economic outcome."
        )

        print(
            "Safe to collapse same Ticker + T_action "
            "to one economic decision."
        )

    print()
    print("D. UNIQUE DECISION BASELINE")
    print("=" * 120)

    print("Unique decisions =", len(unique))
    print("Winners =", int(unique["Winner"].sum()))
    print("Failures =", int(unique["Failure"].sum()))

    print(
        "Win rate = "
        f"{unique['Winner'].mean()*100:.1f}%"
    )

    print(
        "Failure rate = "
        f"{unique['Failure'].mean()*100:.1f}%"
    )

    print()
    print("Unique decisions by ticker:")

    print(
        unique.groupby("Ticker")
        .size()
        .to_string()
    )

    print()
    print("E. CAPITAL-PERMISSION GUARDRAIL")
    print("=" * 120)

    print(
        "Multiple detections may describe richer evidence, "
        "but they do NOT create multiple positions."
    )

    print(
        "Same Ticker + same T_action earns ONE "
        "capital permission."
    )

    print(
        "RawRows is retained as provenance, "
        "not as a sizing multiplier."
    )

    print()
    print("=" * 120)
    print("IDENTITY AUDIT COMPLETE")

    if len(inconsistent):
        print("STATUS: HOLD — IDENTITY CONFLICT REQUIRES REVIEW")
    else:
        print("STATUS: PASS — UNIQUE ECONOMIC DECISIONS CREATED")

    print("=" * 120)


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

if len(inconsistent) == 0:
    unique.to_csv(
        OUT_CSV,
        index=False
    )

    print()
    print("Saved:")
    print(" ", OUT_TXT)
    print(" ", OUT_CSV)

else:
    print()
    print("Saved audit only:")
    print(" ", OUT_TXT)
    print("Unique CSV NOT written because identity conflicts exist.")
