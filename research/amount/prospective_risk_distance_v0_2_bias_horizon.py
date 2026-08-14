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
    "reports/amount/prospective_risk_distance_v0_2_bias_horizon.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_2_bias_horizon.csv"
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
        header=[0, 1],
        index_col=0
    )

    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High", "Low", "Close"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    C = df["Close"]
    L = df["Low"]

    # ========================================================
    # SAME BIAS FAMILY — THREE HORIZONS
    # ========================================================

    bias = {}

    for n in [3, 5, 10]:

        ma = C.rolling(n).mean()

        bias[n] = (
            C / ma - 1
        ) * 100

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
        # FIRST BEARISH ZERO-CROSS FOR EACH BIAS HORIZON
        # ====================================================

        cross = {}

        for n in [3, 5, 10]:

            cross[n] = None

            for j in range(loc + 1, loc + 11):

                if (
                    bias[n].iloc[j] < 0
                    and bias[n].iloc[j - 1] >= 0
                ):
                    cross[n] = j
                    break

        # ====================================================
        # LAGS AND PRICE DISTANCE AT CROSS
        # ====================================================

        def lag(n):

            return (
                cross[n] - loc
                if cross[n] is not None
                else np.nan
            )

        def close_dist(n):

            return (
                (C.iloc[cross[n]] / entry - 1) * 100
                if cross[n] is not None
                else np.nan
            )

        def low_dist(n):

            return (
                (L.iloc[cross[n]] / entry - 1) * 100
                if cross[n] is not None
                else np.nan
            )

        # ====================================================
        # CASCADE DEPTH
        #
        # B3 only:
        # B3 crossed, B5/B10 did not.
        #
        # B3+B5:
        # B3 and B5 crossed, B10 did not.
        #
        # B3+B5+B10:
        # all three crossed.
        #
        # Other orderings are retained separately.
        # ====================================================

        b3 = cross[3] is not None
        b5 = cross[5] is not None
        b10 = cross[10] is not None

        if b3 and not b5 and not b10:
            state = "B3_ONLY"

        elif b3 and b5 and not b10:
            state = "B3_B5"

        elif b3 and b5 and b10:
            state = "B3_B5_B10"

        elif b5 and not b3 and not b10:
            state = "B5_ONLY"

        elif b10 and not b3 and not b5:
            state = "B10_ONLY"

        else:
            state = "OTHER"

        # ====================================================
        # ORDER CHECK
        # ====================================================

        ordered_35 = (
            b3 and b5
            and cross[3] <= cross[5]
        )

        ordered_3510 = (
            b3 and b5 and b10
            and cross[3] <= cross[5] <= cross[10]
        )

        mae10 = (
            L.iloc[loc+1:loc+11].min()
            / entry - 1
        ) * 100

        rows.append({
            "Ticker": ticker,
            "T_action": t,
            "FWD10": e["FWD10"],
            "Winner": e["FWD10"] > 0,
            "MAE10": mae10,

            "B3Cross": b3,
            "B5Cross": b5,
            "B10Cross": b10,

            "B3Lag": lag(3),
            "B5Lag": lag(5),
            "B10Lag": lag(10),

            "B3CloseDist": close_dist(3),
            "B5CloseDist": close_dist(5),
            "B10CloseDist": close_dist(10),

            "B3LowDist": low_dist(3),
            "B5LowDist": low_dist(5),
            "B10LowDist": low_dist(10),

            "Ordered35": ordered_35,
            "Ordered3510": ordered_3510,
            "BiasState": state,
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


def report():

    print("=" * 124)
    print("PROSPECTIVE RISK DISTANCE v0.2")
    print("BIAS MULTI-HORIZON VITAL SIGNS")
    print("BIAS3 -> BIAS5 -> BIAS10")
    print("=" * 124)

    # ========================================================
    # A. CROSS FREQUENCY
    # ========================================================

    print()
    print("A. BEARISH ZERO-CROSS FREQUENCY WITHIN 10D")
    print("=" * 124)

    for n in [3, 5, 10]:

        col = f"B{n}Cross"

        print(
            f"Bias{n:<2} | "
            f"N={int(res[col].sum()):3} / {len(res)} | "
            f"{res[col].mean()*100:5.1f}%"
        )

    # ========================================================
    # B. WINNER vs FAILURE CROSS FREQUENCY
    # ========================================================

    print()
    print("B. CROSS FREQUENCY — WINNERS vs FAILURES")
    print("=" * 124)

    for n in [3, 5, 10]:

        col = f"B{n}Cross"

        w = res[res["Winner"]]
        f = res[~res["Winner"]]

        print(
            f"Bias{n:<2} | "
            f"Winners={w[col].mean()*100:5.1f}% | "
            f"Failures={f[col].mean()*100:5.1f}%"
        )

    # ========================================================
    # C. CASCADE DEPTH
    # ========================================================

    print()
    print("C. BIAS FAMILY CASCADE DEPTH")
    print("=" * 124)

    for state in [
        "B3_ONLY",
        "B3_B5",
        "B3_B5_B10",
        "B5_ONLY",
        "B10_ONLY",
        "OTHER",
    ]:

        group_line(
            state,
            res[
                res["BiasState"] == state
            ]
        )

    # ========================================================
    # D. CROSS TIMING
    # ========================================================

    print()
    print("D. FIRST CROSS TIMING")
    print("=" * 124)

    for n in [3, 5, 10]:

        s = res[f"B{n}Lag"].dropna()

        if len(s):

            print(
                f"Bias{n:<2} | "
                f"N={len(s):3} | "
                f"median={s.median():4.1f}D | "
                f"mean={s.mean():4.1f}D"
            )

    # ========================================================
    # E. PRICE DISTANCE AT CROSS
    # ========================================================

    print()
    print("E. PRICE DISTANCE AT FIRST CROSS")
    print("=" * 124)

    for n in [3, 5, 10]:

        close = res[
            f"B{n}CloseDist"
        ].dropna()

        low = res[
            f"B{n}LowDist"
        ].dropna()

        if len(close):

            print()
            print(
                f"Bias{n}"
            )

            print(
                f" Close | "
                f"median={close.median():6.2f}% | "
                f"mean={close.mean():6.2f}%"
            )

            print(
                f" Low   | "
                f"median={low.median():6.2f}% | "
                f"mean={low.mean():6.2f}%"
            )

    # ========================================================
    # F. ORDERED CASCADE
    # ========================================================

    print()
    print("F. ORDERED CASCADE")
    print("=" * 124)

    group_line(
        "ORDERED B3->B5",
        res[
            res["Ordered35"]
        ]
    )

    group_line(
        "ORDERED 3->5->10",
        res[
            res["Ordered3510"]
        ]
    )

    # ========================================================
    # G. FALSE-ALARM VIEW
    # ========================================================

    print()
    print("G. EVENTUAL WINNERS THAT STILL TRIGGERED EACH WARNING")
    print("=" * 124)

    winners = res[
        res["Winner"]
    ]

    for n in [3, 5, 10]:

        col = f"B{n}Cross"

        count = int(
            winners[col].sum()
        )

        print(
            f"Bias{n:<2} warning among winners | "
            f"N={count:3} / {len(winners)} | "
            f"{winners[col].mean()*100:5.1f}%"
        )

    # ========================================================
    # H. GUARDRAILS
    # ========================================================

    print()
    print("H. INTERPRETATION GUARDRAILS")
    print("=" * 124)

    print(
        "1. Bias3/Bias5/Bias10 are being interviewed, "
        "not promoted."
    )

    print(
        "2. A bearish zero-cross is a warning event, "
        "not an automatic exit."
    )

    print(
        "3. Longer Bias horizons may reduce noise but may "
        "also warn later."
    )

    print(
        "4. Cascade depth must show incremental outcome "
        "discrimination before earning action authority."
    )

    print(
        "5. No fixed price stop is created by this study."
    )

    print()
    print("=" * 124)
    print("PROSPECTIVE RISK DISTANCE v0.2 COMPLETE")
    print(
        "BIAS3 MAY HEAR THE FIRST WHEEZE; "
        "BIAS5 AND BIAS10 ARE TESTED TO SEE WHETHER "
        "THE BREATHING PROBLEM IS ACTUALLY DEEPENING."
    )
    print("=" * 124)


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
