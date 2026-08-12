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
    "reports/amount/prospective_risk_distance_v0_2R_bias_landslide.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_2R_bias_landslide.csv"
)

HORIZONS = [3, 5, 10, 20]

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

    bias = {}

    for n in HORIZONS:
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

        for n in HORIZONS:

            cross[n] = None

            for j in range(
                loc + 1,
                loc + 11
            ):

                if (
                    bias[n].iloc[j] < 0
                    and bias[n].iloc[j - 1] >= 0
                ):
                    cross[n] = j
                    break

        # ====================================================
        # CASCADE DEPTH
        #
        # Depth = longest complete chain from Bias3 upward:
        #
        # 0 = no Bias3 cross
        # 1 = B3 only
        # 2 = B3 + B5
        # 3 = B3 + B5 + B10
        # 4 = B3 + B5 + B10 + B20
        # ====================================================

        b3 = cross[3] is not None
        b5 = cross[5] is not None
        b10 = cross[10] is not None
        b20 = cross[20] is not None

        if not b3:
            depth = 0
        elif b3 and not b5:
            depth = 1
        elif b3 and b5 and not b10:
            depth = 2
        elif b3 and b5 and b10 and not b20:
            depth = 3
        else:
            depth = 4

        # ====================================================
        # ORDER CHECK
        # ====================================================

        ordered35 = (
            b3 and b5
            and cross[3] <= cross[5]
        )

        ordered3510 = (
            b3 and b5 and b10
            and cross[3] <= cross[5] <= cross[10]
        )

        ordered351020 = (
            b3 and b5 and b10 and b20
            and cross[3] <= cross[5]
            <= cross[10] <= cross[20]
        )

        # ====================================================
        # PRICE DISTANCE AT EACH CROSS
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

        mae10 = (
            L.iloc[
                loc + 1:loc + 11
            ].min()
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
            "B20Cross": b20,

            "B3Lag": lag(3),
            "B5Lag": lag(5),
            "B10Lag": lag(10),
            "B20Lag": lag(20),

            "B3CloseDist": close_dist(3),
            "B5CloseDist": close_dist(5),
            "B10CloseDist": close_dist(10),
            "B20CloseDist": close_dist(20),

            "B3LowDist": low_dist(3),
            "B5LowDist": low_dist(5),
            "B10LowDist": low_dist(10),
            "B20LowDist": low_dist(20),

            "CascadeDepth": depth,
            "Ordered35": ordered35,
            "Ordered3510": ordered3510,
            "Ordered351020": ordered351020,
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
        print(f"{name:20} | N=0")
        return

    print(
        f"{name:20} | "
        f"N={len(g):3} | "
        f"winner={g['Winner'].mean()*100:5.1f}% | "
        f"FWD10 mean={g['FWD10'].mean():6.2f}% | "
        f"median={g['FWD10'].median():6.2f}% | "
        f"MAE10 mean={g['MAE10'].mean():6.2f}% | "
        f"median={g['MAE10'].median():6.2f}%"
    )


def report():

    print("=" * 128)
    print("PROSPECTIVE RISK DISTANCE v0.2R")
    print("BIAS LANDSLIDE CASCADE")
    print("BIAS3 -> BIAS5 -> BIAS10 -> BIAS20")
    print("=" * 128)

    # ========================================================
    # A. CROSS FREQUENCY
    # ========================================================

    print()
    print("A. BEARISH ZERO-CROSS FREQUENCY WITHIN 10D")
    print("=" * 128)

    for n in HORIZONS:

        col = f"B{n}Cross"

        print(
            f"Bias{n:<2} | "
            f"N={int(res[col].sum()):3}/{len(res)} | "
            f"{res[col].mean()*100:5.1f}%"
        )

    # ========================================================
    # B. WINNERS vs FAILURES
    # ========================================================

    print()
    print("B. WARNING FREQUENCY — WINNERS vs FAILURES")
    print("=" * 128)

    w = res[res["Winner"]]
    f = res[~res["Winner"]]

    for n in HORIZONS:

        col = f"B{n}Cross"

        print(
            f"Bias{n:<2} | "
            f"Winners={w[col].mean()*100:5.1f}% | "
            f"Failures={f[col].mean()*100:5.1f}% | "
            f"Gap={f[col].mean()*100 - w[col].mean()*100:6.1f}pp"
        )

    # ========================================================
    # C. CASCADE DEPTH
    # ========================================================

    print()
    print("C. LANDSLIDE DEPTH")
    print("=" * 128)

    labels = {
        0: "NO B3 WARNING",
        1: "B3 ONLY",
        2: "B3 -> B5",
        3: "B3 -> B5 -> B10",
        4: "B3 -> B5 -> B10 -> B20",
    }

    for depth in range(5):

        group_line(
            labels[depth],
            res[
                res["CascadeDepth"] == depth
            ]
        )

    # ========================================================
    # D. TIMING
    # ========================================================

    print()
    print("D. FIRST CROSS TIMING")
    print("=" * 128)

    for n in HORIZONS:

        s = res[
            f"B{n}Lag"
        ].dropna()

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
    print("E. PRICE DISTANCE WHEN EACH LAYER TRIGGERS")
    print("=" * 128)

    for n in HORIZONS:

        close = res[
            f"B{n}CloseDist"
        ].dropna()

        low = res[
            f"B{n}LowDist"
        ].dropna()

        if len(close):

            print()
            print(f"Bias{n}")

            print(
                f" Close | "
                f"N={len(close):3} | "
                f"median={close.median():6.2f}% | "
                f"mean={close.mean():6.2f}%"
            )

            print(
                f" Low   | "
                f"N={len(low):3} | "
                f"median={low.median():6.2f}% | "
                f"mean={low.mean():6.2f}%"
            )

    # ========================================================
    # F. ORDERED CASCADE
    # ========================================================

    print()
    print("F. ORDERED CASCADE")
    print("=" * 128)

    group_line(
        "ORDERED 3 -> 5",
        res[res["Ordered35"]]
    )

    group_line(
        "ORDERED 3 -> 5 -> 10",
        res[res["Ordered3510"]]
    )

    group_line(
        "ORDERED 3 -> 5 -> 10 -> 20",
        res[res["Ordered351020"]]
    )

    # ========================================================
    # G. FALSE-ALARM VIEW
    # ========================================================

    print()
    print("G. EVENTUAL WINNERS THAT STILL TRIGGERED EACH LAYER")
    print("=" * 128)

    for n in HORIZONS:

        col = f"B{n}Cross"

        count = int(
            w[col].sum()
        )

        print(
            f"Bias{n:<2} warning among winners | "
            f"N={count:3}/{len(w)} | "
            f"{w[col].mean()*100:5.1f}%"
        )

    # ========================================================
    # H. MONOTONICITY CHECK
    # ========================================================

    print()
    print("H. DOES DEEPER CASCADE LOOK WORSE?")
    print("=" * 128)

    depth_summary = (
        res.groupby("CascadeDepth")
        .agg(
            N=("Winner", "size"),
            WinnerRate=("Winner", "mean"),
            MeanFWD10=("FWD10", "mean"),
            MeanMAE10=("MAE10", "mean")
        )
        .reset_index()
    )

    depth_summary["WinnerRate"] *= 100

    print(
        depth_summary.to_string(
            index=False,
            formatters={
                "WinnerRate":
                    lambda x: f"{x:.1f}%",
                "MeanFWD10":
                    lambda x: f"{x:.2f}%",
                "MeanMAE10":
                    lambda x: f"{x:.2f}%",
            }
        )
    )

    # ========================================================
    # I. GUARDRAILS
    # ========================================================

    print()
    print("I. INTERPRETATION GUARDRAILS")
    print("=" * 128)

    print(
        "1. Bias3/Bias5/Bias10/Bias20 are warning layers, "
        "not automatic exits."
    )

    print(
        "2. Bias20 is NOT assumed to mean thesis invalidation."
    )

    print(
        "3. A deeper cascade must show incremental "
        "outcome discrimination before receiving authority."
    )

    print(
        "4. Longer horizons may improve specificity "
        "at the cost of later warning."
    )

    print(
        "5. No fixed stop-loss percentage is created here."
    )

    print()
    print("=" * 128)
    print("PROSPECTIVE RISK DISTANCE v0.2R COMPLETE")
    print(
        "FIRST MUDDY WATER IS NOT A LANDSLIDE. "
        "THE QUESTION IS WHETHER THE FLOW DEEPENS "
        "FROM BIAS3 TO BIAS20."
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
