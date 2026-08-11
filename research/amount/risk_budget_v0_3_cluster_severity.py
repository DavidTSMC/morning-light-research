import pandas as pd
import numpy as np
from itertools import combinations
from pathlib import Path
from contextlib import redirect_stdout

FILES = {
    "2882": "data/raw/2882_TW_5Y.csv",
    "2330": "data/raw/2330_TW_5Y.csv",
    "2454": "data/raw/2454_TW_5Y.csv",
    "0050": "data/raw/0050_TW_5Y.csv",
    "2603": "data/raw/2603_TW_5Y.csv",
    "2382": "data/raw/2382_TW_5Y.csv",
}

INFILE = Path(
    "reports/amount/risk_budget_v0_1_daily_exposure.csv"
)

OUT_TXT = Path(
    "reports/amount/risk_budget_v0_3_cluster_severity.txt"
)

OUT_CSV = Path(
    "reports/amount/risk_budget_v0_3_cluster_severity.csv"
)

FORWARD_DAYS = 5
DAMAGE = -3.0
SEVERE = -5.0

daily = pd.read_csv(INFILE)
daily["Date"] = pd.to_datetime(daily["Date"])

price_data = {}

for ticker, f in FILES.items():

    df = pd.read_csv(
        f,
        header=[0,1],
        index_col=0
    )

    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High","Low","Close"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    price_data[ticker] = df


# ============================================================
# BUILD DAILY ACTIVE-TICKER MAE MAP
# ============================================================

daily_mae = {}

for _, row in daily.iterrows():

    date = row["Date"]

    active = (
        str(row["ActiveTickers"]).split(",")
        if pd.notna(row["ActiveTickers"])
        and str(row["ActiveTickers"]).strip()
        else []
    )

    active = [
        x for x in active
        if x in FILES
    ]

    d = {}

    for ticker in active:

        df = price_data[ticker]

        if date not in df.index:
            continue

        loc = df.index.get_loc(date)

        if not isinstance(loc, (int, np.integer)):
            continue

        if loc + FORWARD_DAYS >= len(df):
            continue

        close0 = df["Close"].iloc[loc]

        low5 = df["Low"].iloc[
            loc+1:loc+1+FORWARD_DAYS
        ].min()

        mae = (
            low5 / close0 - 1
        ) * 100

        d[ticker] = mae

    daily_mae[date] = d


# ============================================================
# PAIR SEVERITY
#
# Only evaluate days when BOTH pair members are active.
#
# JointDamage:
# both MAE <= -3%
#
# JointSevere:
# both MAE <= -5%
#
# On JointDamage days:
# AveragePairMAE = mean of the two MAEs
# WorstMemberMAE = worse of the two MAEs
# ============================================================

rows = []

for combo in combinations(sorted(FILES.keys()), 2):

    joint_damage_maes = []
    joint_worst = []

    coactive = 0
    joint_damage = 0
    joint_severe = 0

    for date, d in daily_mae.items():

        if not all(t in d for t in combo):
            continue

        coactive += 1

        maes = [
            d[combo[0]],
            d[combo[1]],
        ]

        if all(x <= DAMAGE for x in maes):

            joint_damage += 1

            joint_damage_maes.append(
                np.mean(maes)
            )

            joint_worst.append(
                np.min(maes)
            )

        if all(x <= SEVERE for x in maes):
            joint_severe += 1

    if coactive == 0:
        continue

    rows.append({
        "Cluster": "+".join(combo),
        "CoactiveDays": coactive,
        "JointDamageDays": joint_damage,
        "JointDamageRate":
            joint_damage / coactive * 100,
        "JointSevereDays": joint_severe,
        "JointSevereRate":
            joint_severe / coactive * 100,
        "JointDamageAvgMAE":
            np.mean(joint_damage_maes)
            if joint_damage_maes
            else np.nan,
        "JointDamageMedianMAE":
            np.median(joint_damage_maes)
            if joint_damage_maes
            else np.nan,
        "WorstMemberMeanMAE":
            np.mean(joint_worst)
            if joint_worst
            else np.nan,
        "WorstMemberMedianMAE":
            np.median(joint_worst)
            if joint_worst
            else np.nan,
    })

res = pd.DataFrame(rows)

OUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

res.to_csv(
    OUT_CSV,
    index=False
)


# ============================================================
# REPORT
# ============================================================

def report():

    print("=" * 122)
    print("RISK BUDGET v0.3 — CLUSTER SEVERITY / JOINT TAIL")
    print("SOURCE: FROZEN v0.1 DAILY A2 EXPOSURE MAP")
    print("JOINT DAMAGE = BOTH NEXT-5D MAE <= -3%")
    print("JOINT SEVERE = BOTH NEXT-5D MAE <= -5%")
    print("NO NEW INDICATORS OR A2 DEFINITIONS")
    print("=" * 122)

    eligible = res[
        res.CoactiveDays >= 10
    ].copy()

    # ========================================================
    # A. JOINT-DAMAGE SEVERITY
    # ========================================================

    print()
    print("A. JOINT-DAMAGE SEVERITY")
    print("MINIMUM CO-ACTIVE DAYS = 10")
    print("=" * 122)

    a = eligible.sort_values(
        [
            "JointDamageAvgMAE",
            "JointDamageRate"
        ],
        ascending=[True, False]
    )

    for _, r in a.iterrows():

        print(
            f"{r.Cluster:12} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"jointN={int(r.JointDamageDays):2} | "
            f"joint_rate={r.JointDamageRate:5.1f}% | "
            f"avg_pair_MAE={r.JointDamageAvgMAE:6.2f}% | "
            f"worst_member={r.WorstMemberMeanMAE:6.2f}%"
        )

    # ========================================================
    # B. JOINT SEVERE TAIL
    # ========================================================

    print()
    print("B. BOTH <= -5% — JOINT SEVERE TAIL")
    print("=" * 122)

    b = eligible.sort_values(
        [
            "JointSevereRate",
            "CoactiveDays"
        ],
        ascending=[False, False]
    )

    for _, r in b.iterrows():

        print(
            f"{r.Cluster:12} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"severeN={int(r.JointSevereDays):2} | "
            f"BOTH<=-5%={r.JointSevereRate:5.1f}% | "
            f"joint>=-3%={r.JointDamageRate:5.1f}%"
        )

    # ========================================================
    # C. FREQUENCY × SEVERITY VIEW
    # ========================================================

    print()
    print("C. FREQUENCY × SEVERITY")
    print("=" * 122)

    c = eligible[
        eligible.JointDamageDays >= 2
    ].copy()

    if len(c):

        c["SeverityScore"] = (
            c["JointDamageRate"]
            * abs(c["JointDamageAvgMAE"])
        )

        c = c.sort_values(
            "SeverityScore",
            ascending=False
        )

        for _, r in c.iterrows():

            print(
                f"{r.Cluster:12} | "
                f"Ndays={int(r.CoactiveDays):3} | "
                f"joint_rate={r.JointDamageRate:5.1f}% | "
                f"avg_joint_MAE={r.JointDamageAvgMAE:6.2f}% | "
                f"severity_index={r.SeverityScore:6.1f}"
            )

    # ========================================================
    # D. SPECIAL PAIRS
    # ========================================================

    print()
    print("D. SPECIAL PAIRS")
    print("=" * 122)

    specials = [
        "0050+2330",
        "0050+2454",
        "0050+2603",
        "0050+2382",
        "2330+2454",
        "2454+2603",
        "2382+2603",
    ]

    for cluster in specials:

        g = res[
            res.Cluster == cluster
        ]

        if not len(g):
            continue

        r = g.iloc[0]

        print(
            f"{cluster:12} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"joint={r.JointDamageRate:5.1f}% | "
            f"both<=-5={r.JointSevereRate:5.1f}% | "
            f"avg_joint_MAE={r.JointDamageAvgMAE:6.2f}% | "
            f"worst={r.WorstMemberMeanMAE:6.2f}%"
        )

    # ========================================================
    # E. INTERPRETATION GUARDRAIL
    # ========================================================

    print()
    print("E. INTERPRETATION GUARDRAIL")
    print("=" * 122)

    print(
        "Frequency alone does not define cluster risk."
    )
    print(
        "Severity alone does not define cluster risk."
    )
    print(
        "A useful cluster ceiling requires BOTH recurrence and meaningful joint downside."
    )
    print()
    print(
        "SeverityScore is descriptive only and MUST NOT be used as a production sizing formula."
    )

    # ========================================================
    # F. REPRODUCIBILITY
    # ========================================================

    print()
    print("F. REPRODUCIBILITY RECORD")
    print("=" * 122)

    print("SCRIPT =", __file__)
    print("OUTPUT CSV =", OUT_CSV)
    print("PAIR CLUSTERS =", len(res))

    print()
    print("=" * 122)
    print("RISK BUDGET v0.3 COMPLETE")
    print("QUESTION: WHEN A CLUSTER IS HURT TOGETHER, HOW DEEP IS THE JOINT DAMAGE?")
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
