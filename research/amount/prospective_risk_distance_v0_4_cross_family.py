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
    "reports/amount/prospective_risk_distance_v0_4_cross_family.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_4_cross_family.csv"
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
    # BIAS10
    # ========================================================

    ma10 = C.rolling(10).mean()
    bias10 = (C / ma10 - 1) * 100

    # ========================================================
    # D-M
    # ========================================================

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

    # ========================================================
    # J
    #
    # Standard stochastic J from K/D.
    # Research warning = local downward A-turn proxy:
    # yesterday J > day-before J AND today J < yesterday J.
    #
    # This is descriptive interview logic only.
    # ========================================================

    low9 = L.rolling(9).min()
    high9 = H.rolling(9).max()

    rsv = (
        (C - low9)
        / (high9 - low9)
        * 100
    )

    K = rsv.ewm(
        alpha=1/3,
        adjust=False
    ).mean()

    D = K.ewm(
        alpha=1/3,
        adjust=False
    ).mean()

    J = 3 * K - 2 * D

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
        # FIRST WARNING WITHIN 10D
        # ====================================================

        b10_i = None
        dm_i = None
        j_i = None

        for j in range(loc+1, loc+11):

            if (
                b10_i is None
                and bias10.iloc[j] < 0
                and bias10.iloc[j-1] >= 0
            ):
                b10_i = j

            if (
                dm_i is None
                and dm.iloc[j] < 0
                and dm.iloc[j-1] >= 0
            ):
                dm_i = j

            if (
                j_i is None
                and j >= 2
                and J.iloc[j-1] > J.iloc[j-2]
                and J.iloc[j] < J.iloc[j-1]
            ):
                j_i = j

        def lag(idx):
            return (
                idx - loc
                if idx is not None
                else np.nan
            )

        def close_dist(idx):
            return (
                (C.iloc[idx] / entry - 1) * 100
                if idx is not None
                else np.nan
            )

        def low_dist(idx):
            return (
                (L.iloc[idx] / entry - 1) * 100
                if idx is not None
                else np.nan
            )

        mae10 = (
            L.iloc[loc+1:loc+11].min()
            / entry - 1
        ) * 100

        # ====================================================
        # LEAD / LAG
        # ====================================================

        warning_list = []

        if j_i is not None:
            warning_list.append(("J", j_i))

        if b10_i is not None:
            warning_list.append(("BIAS10", b10_i))

        if dm_i is not None:
            warning_list.append(("DM", dm_i))

        if warning_list:

            warning_list.sort(
                key=lambda x: x[1]
            )

            first_family = warning_list[0][0]

        else:

            first_family = "NONE"

        # ====================================================
        # COMBINATIONS
        # ====================================================

        has_j = j_i is not None
        has_b10 = b10_i is not None
        has_dm = dm_i is not None

        combo_count = (
            int(has_j)
            + int(has_b10)
            + int(has_dm)
        )

        if has_j and has_b10 and has_dm:
            combo = "J+B10+DM"

        elif has_j and has_b10:
            combo = "J+B10"

        elif has_b10 and has_dm:
            combo = "B10+DM"

        elif has_j and has_dm:
            combo = "J+DM"

        elif has_j:
            combo = "J_ONLY"

        elif has_b10:
            combo = "B10_ONLY"

        elif has_dm:
            combo = "DM_ONLY"

        else:
            combo = "NONE"

        rows.append({
            "Ticker": ticker,
            "T_action": t,
            "Winner": e["FWD10"] > 0,
            "FWD10": e["FWD10"],
            "MAE10": mae10,

            "JWarn": has_j,
            "B10Warn": has_b10,
            "DMWarn": has_dm,

            "JLag": lag(j_i),
            "B10Lag": lag(b10_i),
            "DMLag": lag(dm_i),

            "JCloseDist": close_dist(j_i),
            "B10CloseDist": close_dist(b10_i),
            "DMCloseDist": close_dist(dm_i),

            "JLowDist": low_dist(j_i),
            "B10LowDist": low_dist(b10_i),
            "DMLowDist": low_dist(dm_i),

            "FirstFamily": first_family,
            "ComboCount": combo_count,
            "Combo": combo,
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
        f"{name:16} | "
        f"N={len(g):3} | "
        f"winner={g['Winner'].mean()*100:5.1f}% | "
        f"FWD10 mean={g['FWD10'].mean():6.2f}% | "
        f"median={g['FWD10'].median():6.2f}% | "
        f"MAE10 mean={g['MAE10'].mean():6.2f}%"
    )


def stats(s):

    s = s.dropna()

    if len(s) == 0:
        return "N=0"

    return (
        f"N={len(s):3} | "
        f"median={s.median():5.1f} | "
        f"mean={s.mean():5.1f}"
    )


def report():

    print("=" * 128)
    print("PROSPECTIVE RISK DISTANCE v0.4")
    print("CROSS-FAMILY MEDICAL BOARD")
    print("J vs BIAS10 vs D-M")
    print("=" * 128)

    # ========================================================
    # A. WARNING FREQUENCY
    # ========================================================

    print()
    print("A. WARNING FREQUENCY — WINNERS vs FAILURES")
    print("=" * 128)

    w = res[res["Winner"]]
    f = res[~res["Winner"]]

    mapping = {
        "J": "JWarn",
        "BIAS10": "B10Warn",
        "D-M": "DMWarn",
    }

    for name, col in mapping.items():

        wr = w[col].mean() * 100
        fr = f[col].mean() * 100

        print(
            f"{name:8} | "
            f"Winner={wr:5.1f}% | "
            f"Failure={fr:5.1f}% | "
            f"Gap={fr-wr:+6.1f} pp"
        )

    # ========================================================
    # B. TIMING
    # ========================================================

    print()
    print("B. FIRST WARNING TIMING")
    print("=" * 128)

    print(
        "J      | "
        + stats(res["JLag"])
    )

    print(
        "BIAS10 | "
        + stats(res["B10Lag"])
    )

    print(
        "D-M    | "
        + stats(res["DMLag"])
    )

    # ========================================================
    # C. PRICE DISTANCE AT WARNING
    # ========================================================

    print()
    print("C. PRICE DISTANCE AT FIRST WARNING")
    print("=" * 128)

    for name, prefix in [
        ("J", "J"),
        ("BIAS10", "B10"),
        ("D-M", "DM"),
    ]:

        close = res[
            f"{prefix}CloseDist"
        ].dropna()

        low = res[
            f"{prefix}LowDist"
        ].dropna()

        if len(close):

            print()
            print(name)

            print(
                f" Close median={close.median():6.2f}% | "
                f"mean={close.mean():6.2f}%"
            )

            print(
                f" Low   median={low.median():6.2f}% | "
                f"mean={low.mean():6.2f}%"
            )

    # ========================================================
    # D. WHO WARNS FIRST?
    # ========================================================

    print()
    print("D. FIRST FAMILY TO WARN")
    print("=" * 128)

    print(
        res["FirstFamily"]
        .value_counts()
        .to_string()
    )

    # ========================================================
    # E. COMBINATION OUTCOME
    # ========================================================

    print()
    print("E. COMBINATION OUTCOME")
    print("=" * 128)

    order = [
        "J_ONLY",
        "B10_ONLY",
        "DM_ONLY",
        "J+B10",
        "J+DM",
        "B10+DM",
        "J+B10+DM",
        "NONE",
    ]

    for combo in order:

        group_line(
            combo,
            res[
                res["Combo"] == combo
            ]
        )

    # ========================================================
    # F. NUMBER OF CONFIRMING FAMILIES
    # ========================================================

    print()
    print("F. CONFIRMATION DEPTH")
    print("=" * 128)

    for n in [0, 1, 2, 3]:

        group_line(
            f"{n} FAMILY",
            res[
                res["ComboCount"] == n
            ]
        )

    # ========================================================
    # G. BIAS10 INCREMENTAL CONFIRMATION
    # ========================================================

    print()
    print("G. BIAS10 + CROSS-FAMILY CONFIRMATION")
    print("=" * 128)

    b = res[
        res["B10Warn"]
    ]

    group_line(
        "B10 TOTAL",
        b
    )

    group_line(
        "B10 + J",
        b[
            b["JWarn"]
        ]
    )

    group_line(
        "B10 + DM",
        b[
            b["DMWarn"]
        ]
    )

    group_line(
        "B10 + J + DM",
        b[
            b["JWarn"]
            & b["DMWarn"]
        ]
    )

    # ========================================================
    # H. GUARDRAILS
    # ========================================================

    print()
    print("H. INTERPRETATION GUARDRAILS")
    print("=" * 128)

    print(
        "1. J A-turn proxy is a research interview definition, "
        "not a production exit rule."
    )

    print(
        "2. BIAS10 and D-M use bearish zero-cross state changes."
    )

    print(
        "3. Warning frequency must be judged together with timing."
    )

    print(
        "4. Cross-family confirmation must show incremental "
        "outcome discrimination before receiving action authority."
    )

    print(
        "5. No single warning automatically means full exit."
    )

    print()
    print("=" * 128)
    print("PROSPECTIVE RISK DISTANCE v0.4 COMPLETE")
    print(
        "WHO CALLS FIRST? WHO IS RIGHT? "
        "WHO CONFIRMS THESIS INJURY BEFORE IT IS TOO LATE?"
    )
    print("=" * 128)


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
