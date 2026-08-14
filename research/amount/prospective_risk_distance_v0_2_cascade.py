import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

EPFILE = Path(
    "reports/amount/individual_risk_budget_v0_5R_unique_episodes.csv"
)

FILES = {
    "2882": "data/raw/2882_TW_5Y.csv",
    "2330": "data/raw/2330_TW_5Y.csv",
    "2454": "data/raw/2454_TW_5Y.csv",
    "0050": "data/raw/0050_TW_5Y.csv",
    "2603": "data/raw/2603_TW_5Y.csv",
    "2382": "data/raw/2382_TW_5Y.csv",
}

OUT_TXT = Path(
    "reports/amount/prospective_risk_distance_v0_2_cascade.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_2_cascade.csv"
)

ep = pd.read_csv(
    EPFILE,
    dtype={"Ticker": str}
)

ep["Ticker"] = ep["Ticker"].str.zfill(4)
ep["T_action"] = pd.to_datetime(ep["T_action"])

rows = []

for ticker, f in FILES.items():

    df = pd.read_csv(
        f,
        header=[0,1],
        index_col=0
    )

    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High", "Low", "Close"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    H = df["High"]
    L = df["Low"]
    C = df["Close"]

    # ========================================================
    # REAL-TIME INDICATORS
    # ========================================================

    ma3 = C.rolling(3).mean()
    bias3 = (C / ma3 - 1) * 100

    mtm3 = C - C.shift(3)

    ema12 = C.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = C.ewm(
        span=26,
        adjust=False
    ).mean()

    dif = ema12 - ema26

    sig = dif.ewm(
        span=9,
        adjust=False
    ).mean()

    dm = dif - sig

    ticker_ep = ep[
        ep["Ticker"] == ticker
    ]

    for _, e in ticker_ep.iterrows():

        t = e["T_action"]

        if t not in df.index:
            continue

        loc = df.index.get_loc(t)

        if not isinstance(
            loc,
            (int, np.integer)
        ):
            continue

        if loc + 10 >= len(df):
            continue

        entry = C.iloc[loc]

        # ====================================================
        # FIRST BIAS3 BEARISH ZERO-CROSS
        # ====================================================

        warning = None

        for j in range(loc+1, loc+11):

            if (
                bias3.iloc[j] < 0
                and bias3.iloc[j-1] >= 0
            ):
                warning = j
                break

        if warning is None:
            continue

        # ====================================================
        # PERSISTENCE
        #
        # Count consecutive closes with Bias3 < 0
        # starting at first warning.
        # ====================================================

        persistence = 0

        for j in range(warning, loc+11):

            if bias3.iloc[j] < 0:
                persistence += 1
            else:
                break

        # ====================================================
        # RECOVERY
        #
        # First day Bias3 returns >= 0 after warning.
        # ====================================================

        recovery = None

        for j in range(warning+1, loc+11):

            if bias3.iloc[j] >= 0:
                recovery = j
                break

        recovery_lag = (
            recovery - warning
            if recovery is not None
            else np.nan
        )

        # ====================================================
        # CASCADE AFTER BIAS3 WARNING
        #
        # Does MTM3 become negative?
        # Does D-M become negative?
        #
        # We look only AFTER warning and within 10D horizon.
        # ====================================================

        mtm_follow = None
        dm_follow = None

        for j in range(warning, loc+11):

            if (
                mtm_follow is None
                and mtm3.iloc[j] < 0
            ):
                mtm_follow = j

            if (
                dm_follow is None
                and dm.iloc[j] < 0
            ):
                dm_follow = j

        mtm_lag = (
            mtm_follow - warning
            if mtm_follow is not None
            else np.nan
        )

        dm_lag = (
            dm_follow - warning
            if dm_follow is not None
            else np.nan
        )

        # ====================================================
        # PRICE DAMAGE AFTER WARNING
        # ====================================================

        warning_close_dist = (
            C.iloc[warning] / entry - 1
        ) * 100

        warning_low_dist = (
            L.iloc[warning] / entry - 1
        ) * 100

        post_warning_low = (
            L.iloc[warning:loc+11].min()
        )

        post_warning_mae = (
            post_warning_low / entry - 1
        ) * 100

        # ====================================================
        # SIMPLE STATE LABELS — DESCRIPTIVE ONLY
        #
        # TRANSIENT:
        # Bias3 warning recovers next day.
        #
        # PERSISTENT:
        # Bias3 remains negative >=2 consecutive days.
        #
        # CASCADE_2:
        # Bias3 warning + either MTM3 or D-M negative.
        #
        # CASCADE_3:
        # Bias3 warning + MTM3 negative + D-M negative.
        #
        # These are research labels, NOT action rules.
        # ====================================================

        transient = (
            recovery_lag == 1
        )

        persistent = (
            persistence >= 2
        )

        cascade2 = (
            mtm_follow is not None
            or dm_follow is not None
        )

        cascade3 = (
            mtm_follow is not None
            and dm_follow is not None
        )

        if cascade3:
            state = "CASCADE_3"
        elif cascade2:
            state = "CASCADE_2"
        elif persistent:
            state = "PERSISTENT_BIAS"
        else:
            state = "TRANSIENT_BIAS"

        rows.append({
            "Ticker": ticker,
            "T_action": t,
            "FWD10": e["FWD10"],
            "Winner": e["FWD10"] > 0,
            "WarningDate": df.index[warning],
            "WarningLag": warning - loc,
            "BiasPersistence": persistence,
            "RecoveryLag": recovery_lag,
            "MTMFollowLag": mtm_lag,
            "DMFollowLag": dm_lag,
            "WarningCloseDist": warning_close_dist,
            "WarningLowDist": warning_low_dist,
            "PostWarningMAE": post_warning_mae,
            "Transient": transient,
            "Persistent": persistent,
            "Cascade2": cascade2,
            "Cascade3": cascade3,
            "State": state,
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


def group_line(name, g):

    if len(g) == 0:
        return

    print(
        f"{name:18} | "
        f"N={len(g):3} | "
        f"winner={g['Winner'].mean()*100:5.1f}% | "
        f"FWD10 mean={g['FWD10'].mean():6.2f}% | "
        f"median={g['FWD10'].median():6.2f}% | "
        f"postWarnMAE mean={g['PostWarningMAE'].mean():6.2f}% | "
        f"median={g['PostWarningMAE'].median():6.2f}%"
    )


def report():

    print("=" * 126)
    print("PROSPECTIVE RISK DISTANCE v0.2")
    print("WHEN DOES A WARNING BECOME AN INJURY?")
    print("BIAS3 PERSISTENCE + MTM3 / D-M CASCADE")
    print("=" * 126)

    # ========================================================
    # A. BASELINE
    # ========================================================

    print()
    print("A. WARNING BASELINE")
    print("=" * 126)

    print("Episodes with Bias3 warning =", len(res))

    print(
        "Winner rate = "
        f"{res['Winner'].mean()*100:.1f}%"
    )

    print()
    print("State counts:")
    print(
        res["State"]
        .value_counts()
        .to_string()
    )

    # ========================================================
    # B. PERSISTENCE
    # ========================================================

    print()
    print("B. BIAS3 WARNING PERSISTENCE")
    print("=" * 126)

    group_line(
        "1 DAY / TRANSIENT",
        res[res["BiasPersistence"] == 1]
    )

    group_line(
        "2 DAYS",
        res[res["BiasPersistence"] == 2]
    )

    group_line(
        "3+ DAYS",
        res[res["BiasPersistence"] >= 3]
    )

    # ========================================================
    # C. CASCADE DEPTH
    # ========================================================

    print()
    print("C. CASCADE DEPTH")
    print("=" * 126)

    group_line(
        "BIAS ONLY",
        res[
            (~res["Cascade2"])
        ]
    )

    group_line(
        "BIAS + >=1",
        res[
            res["Cascade2"]
            & ~res["Cascade3"]
        ]
    )

    group_line(
        "BIAS + MTM + DM",
        res[
            res["Cascade3"]
        ]
    )

    # ========================================================
    # D. RECOVERY SPEED
    # ========================================================

    print()
    print("D. RECOVERY SPEED")
    print("=" * 126)

    group_line(
        "RECOVER NEXT DAY",
        res[
            res["RecoveryLag"] == 1
        ]
    )

    group_line(
        "RECOVER 2-3D",
        res[
            res["RecoveryLag"].between(
                2, 3,
                inclusive="both"
            )
        ]
    )

    group_line(
        "RECOVER >=4D/NONE",
        res[
            (res["RecoveryLag"] >= 4)
            | res["RecoveryLag"].isna()
        ]
    )

    # ========================================================
    # E. CASCADE TIMING
    # ========================================================

    print()
    print("E. FOLLOW-THROUGH TIMING AFTER BIAS3 WARNING")
    print("=" * 126)

    mtm = res["MTMFollowLag"].dropna()
    dm_follow = res["DMFollowLag"].dropna()

    if len(mtm):
        print(
            f"MTM3 follow | N={len(mtm)} | "
            f"median lag={mtm.median():.1f}D | "
            f"mean lag={mtm.mean():.1f}D"
        )

    if len(dm_follow):
        print(
            f"D-M follow  | N={len(dm_follow)} | "
            f"median lag={dm_follow.median():.1f}D | "
            f"mean lag={dm_follow.mean():.1f}D"
        )

    # ========================================================
    # F. STATE OUTCOME
    # ========================================================

    print()
    print("F. DESCRIPTIVE STATE OUTCOME")
    print("=" * 126)

    for state in [
        "TRANSIENT_BIAS",
        "PERSISTENT_BIAS",
        "CASCADE_2",
        "CASCADE_3",
    ]:

        group_line(
            state,
            res[
                res["State"] == state
            ]
        )

    # ========================================================
    # G. GUARDRAILS
    # ========================================================

    print()
    print("G. INTERPRETATION GUARDRAILS")
    print("=" * 126)

    print(
        "1. State labels are descriptive research buckets, "
        "NOT production exit rules."
    )

    print(
        "2. Bias3 warning retains Early-Warning authority only."
    )

    print(
        "3. Persistence and cascade are tested for incremental "
        "information before receiving action authority."
    )

    print(
        "4. No fixed price stop is inferred from this study."
    )

    print(
        "5. All warning/cascade observations are knowable "
        "in real time as they occur."
    )

    print()
    print("=" * 126)
    print("PROSPECTIVE RISK DISTANCE v0.2 COMPLETE")
    print(
        "BIAS3 CALLS THE DOCTOR; "
        "PERSISTENCE AND CASCADE DETERMINE WHETHER "
        "THE PATIENT IS ACTUALLY GETTING SICKER."
    )
    print("=" * 126)


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
