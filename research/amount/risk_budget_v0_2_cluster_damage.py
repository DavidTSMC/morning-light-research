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
    "reports/amount/risk_budget_v0_2_cluster_damage.txt"
)

OUT_CSV = Path(
    "reports/amount/risk_budget_v0_2_cluster_damage.csv"
)

DAMAGE_THRESHOLD = -3.0
FORWARD_DAYS = 5

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
# 1. CALCULATE EACH STOCK'S NEXT-5D MAE FOR EACH DAY
# ============================================================

mae_records = {}

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

    day_mae = {}

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

        low_fwd = df["Low"].iloc[
            loc+1:loc+1+FORWARD_DAYS
        ].min()

        mae = (
            low_fwd / close0 - 1
        ) * 100

        day_mae[ticker] = mae

    mae_records[date] = day_mae


# ============================================================
# 2. TEST ALL PAIRS + TRIPLES
#
# A cluster-day qualifies only when ALL members are active.
#
# Joint damage:
# ALL members have next-5D MAE <= -3%.
# ============================================================

rows = []

tickers = list(FILES.keys())

for size in [2,3]:

    for combo in combinations(tickers, size):

        combo = tuple(sorted(combo))

        coactive_days = 0
        joint_damage_days = 0
        any_damage_days = 0
        total_damaged_members = 0

        member_maes = []

        for date, day_mae in mae_records.items():

            if not all(
                t in day_mae
                for t in combo
            ):
                continue

            coactive_days += 1

            maes = [
                day_mae[t]
                for t in combo
            ]

            member_maes.extend(maes)

            damaged = [
                x <= DAMAGE_THRESHOLD
                for x in maes
            ]

            n_damaged = sum(damaged)

            total_damaged_members += n_damaged

            if n_damaged >= 1:
                any_damage_days += 1

            if n_damaged == size:
                joint_damage_days += 1

        if coactive_days == 0:
            continue

        rows.append({
            "Size": size,
            "Cluster": "+".join(combo),
            "CoactiveDays": coactive_days,
            "AnyDamageDays": any_damage_days,
            "JointDamageDays": joint_damage_days,
            "AnyDamageRate":
                any_damage_days / coactive_days * 100,
            "JointDamageRate":
                joint_damage_days / coactive_days * 100,
            "AvgDamagedMembers":
                total_damaged_members / coactive_days,
            "MeanMemberMAE":
                np.mean(member_maes)
                if member_maes else np.nan,
            "MedianMemberMAE":
                np.median(member_maes)
                if member_maes else np.nan,
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
    print("RISK BUDGET v0.2 — CLUSTER DAMAGE MAP / CABBAGE TEST")
    print("SOURCE: FROZEN v0.1 DAILY A2 EXPOSURE MAP")
    print("DAMAGE = NEXT-5D MAE <= -3%")
    print("NO CORRELATION MATRIX | NO POSITION-SIZE ASSUMPTIONS")
    print("=" * 122)

    # ========================================================
    # A. PAIRS — MOST FREQUENTLY CO-ACTIVE
    # ========================================================

    print()
    print("A. PAIRS — MOST FREQUENTLY CO-ACTIVE")
    print("=" * 122)

    pairs = res[
        res.Size == 2
    ].sort_values(
        "CoactiveDays",
        ascending=False
    )

    for _, r in pairs.head(15).iterrows():

        print(
            f"{r.Cluster:12} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"any_damage={r.AnyDamageRate:5.1f}% | "
            f"JOINT_DAMAGE={r.JointDamageRate:5.1f}% | "
            f"avg_damaged={r.AvgDamagedMembers:4.2f} | "
            f"mean_MAE={r.MeanMemberMAE:6.2f}%"
        )

    # ========================================================
    # B. PAIRS — HIGHEST JOINT DAMAGE
    #
    # Minimum 10 co-active days to avoid tiny-sample leaders.
    # ========================================================

    print()
    print("B. PAIRS — HIGHEST JOINT-DAMAGE RATE")
    print("MINIMUM CO-ACTIVE DAYS = 10")
    print("=" * 122)

    eligible_pairs = pairs[
        pairs.CoactiveDays >= 10
    ].sort_values(
        [
            "JointDamageRate",
            "CoactiveDays"
        ],
        ascending=[False, False]
    )

    for _, r in eligible_pairs.iterrows():

        print(
            f"{r.Cluster:12} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"JOINT_DAMAGE={r.JointDamageRate:5.1f}% | "
            f"any_damage={r.AnyDamageRate:5.1f}% | "
            f"mean_MAE={r.MeanMemberMAE:6.2f}%"
        )

    # ========================================================
    # C. TRIPLES
    # ========================================================

    print()
    print("C. TRIPLES — MOST FREQUENTLY CO-ACTIVE")
    print("=" * 122)

    triples = res[
        res.Size == 3
    ].sort_values(
        "CoactiveDays",
        ascending=False
    )

    for _, r in triples.head(15).iterrows():

        print(
            f"{r.Cluster:17} | "
            f"Ndays={int(r.CoactiveDays):3} | "
            f"any_damage={r.AnyDamageRate:5.1f}% | "
            f"ALL3_DAMAGE={r.JointDamageRate:5.1f}% | "
            f"avg_damaged={r.AvgDamagedMembers:4.2f} | "
            f"mean_MAE={r.MeanMemberMAE:6.2f}%"
        )

    # ========================================================
    # D. CABBAGE TEST — FREQUENCY × JOINT DAMAGE
    #
    # Descriptive only:
    # no threshold is used to create a production cluster.
    # ========================================================

    print()
    print("D. CABBAGE TEST — HIGH FREQUENCY + HIGH JOINT DAMAGE")
    print("=" * 122)

    if len(eligible_pairs):

        freq_median = (
            eligible_pairs.CoactiveDays.median()
        )

        damage_median = (
            eligible_pairs.JointDamageRate.median()
        )

        print(
            f"Descriptive pair medians: "
            f"coactive_days={freq_median:.1f}, "
            f"joint_damage={damage_median:.1f}%"
        )

        print()
        print(
            "Pairs above BOTH medians "
            "(descriptive candidates only):"
        )

        candidates = eligible_pairs[
            (eligible_pairs.CoactiveDays >= freq_median)
            &
            (eligible_pairs.JointDamageRate >= damage_median)
        ]

        if len(candidates):

            for _, r in candidates.iterrows():

                print(
                    f"{r.Cluster:12} | "
                    f"Ndays={int(r.CoactiveDays):3} | "
                    f"joint_damage={r.JointDamageRate:5.1f}%"
                )

        else:
            print("None.")

    # ========================================================
    # E. 0050 + 2330 SPECIAL LOOK-THROUGH CHECK
    # ========================================================

    print()
    print("E. 0050 + 2330 SPECIAL CHECK")
    print("=" * 122)

    special = res[
        res.Cluster == "0050+2330"
    ]

    if len(special):

        r = special.iloc[0]

        print(
            f"Co-active days      = {int(r.CoactiveDays)}"
        )

        print(
            f"Any damage rate     = {r.AnyDamageRate:.1f}%"
        )

        print(
            f"Both damaged rate   = {r.JointDamageRate:.1f}%"
        )

        print(
            f"Mean member MAE     = {r.MeanMemberMAE:.2f}%"
        )

    else:
        print("No co-active observations.")

    # ========================================================
    # F. REPRODUCIBILITY
    # ========================================================

    print()
    print("F. REPRODUCIBILITY RECORD")
    print("=" * 122)

    print("SCRIPT =", __file__)
    print("OUTPUT CSV =", OUT_CSV)
    print("CLUSTERS TESTED =", len(res))

    print()
    print("=" * 122)
    print("RISK BUDGET v0.2 COMPLETE")
    print("CO-ACTIVITY IS NOT ENOUGH.")
    print("CLUSTER RISK REQUIRES OBSERVED JOINT DOWNSIDE.")
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
