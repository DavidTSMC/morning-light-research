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
    "reports/amount/prospective_risk_distance_v0_1.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_1.csv"
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

    for c in ["High","Low","Close"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    H = df["High"]
    L = df["Low"]
    C = df["Close"]

    # ========================================================
    # REAL-TIME INDICATORS
    # All values are known at each day's close.
    # ========================================================

    # Bias3
    ma3 = C.rolling(3).mean()
    bias3 = (C / ma3 - 1) * 100

    # MTM3
    mtm3 = C - C.shift(3)

    # D-M
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

        # --------------------------------------------
        # Forward 10D path
        # --------------------------------------------

        path_lows = L.iloc[
            loc+1:loc+11
        ]

        mae10 = (
            path_lows.min()
            / entry - 1
        ) * 100

        # --------------------------------------------
        # First bearish zero-cross AFTER T_action
        # --------------------------------------------

        bias_day = None
        mtm_day = None
        dm_day = None

        for j in range(loc+1, loc+11):

            if (
                bias_day is None
                and bias3.iloc[j] < 0
                and bias3.iloc[j-1] >= 0
            ):
                bias_day = j

            if (
                mtm_day is None
                and mtm3.iloc[j] < 0
                and mtm3.iloc[j-1] >= 0
            ):
                mtm_day = j

            if (
                dm_day is None
                and dm.iloc[j] < 0
                and dm.iloc[j-1] >= 0
            ):
                dm_day = j

        deterioration_days = [
            x for x in [
                bias_day,
                mtm_day,
                dm_day
            ]
            if x is not None
        ]

        first_det = (
            min(deterioration_days)
            if deterioration_days
            else None
        )

        # --------------------------------------------
        # BREATHING DISTANCE:
        # deepest Low BEFORE first deterioration.
        #
        # If no deterioration in 10D:
        # entire 10D is treated as intact observation.
        # --------------------------------------------

        if first_det is None:

            intact_end = loc + 10

        else:

            intact_end = first_det - 1

        if intact_end >= loc + 1:

            intact_low = L.iloc[
                loc+1:intact_end+1
            ].min()

            intact_mae = (
                intact_low / entry - 1
            ) * 100

        else:

            intact_mae = 0.0

        # --------------------------------------------
        # Distance AT first deterioration close
        # --------------------------------------------

        if first_det is not None:

            det_close_dist = (
                C.iloc[first_det]
                / entry - 1
            ) * 100

            det_low_dist = (
                L.iloc[first_det]
                / entry - 1
            ) * 100

            det_lag = (
                first_det - loc
            )

            if first_det == bias_day:
                first_signal = "BIAS3"
            elif first_det == mtm_day:
                first_signal = "MTM3"
            else:
                first_signal = "DM"

        else:

            det_close_dist = np.nan
            det_low_dist = np.nan
            det_lag = np.nan
            first_signal = "NONE"

        rows.append({
            "Ticker": ticker,
            "T_action": t,
            "FWD10": e["FWD10"],
            "Winner": e["FWD10"] > 0,
            "MAE10": mae10,
            "IntactBreathingMAE":
                intact_mae,
            "FirstDeterioration":
                first_signal,
            "DeteriorationLag":
                det_lag,
            "DistanceAtDetClose":
                det_close_dist,
            "DistanceAtDetLow":
                det_low_dist,
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


def describe(s):

    s = s.dropna()

    if len(s) == 0:
        return "N=0"

    return (
        f"N={len(s):3} | "
        f"mean={s.mean():6.2f}% | "
        f"median={s.median():6.2f}% | "
        f"P25={s.quantile(.25):6.2f}% | "
        f"P10={s.quantile(.10):6.2f}% | "
        f"min={s.min():6.2f}%"
    )


def report():

    print("=" * 124)
    print("PROSPECTIVE RISK DISTANCE v0.1")
    print("NORMAL BREATHING vs THESIS DETERIORATION")
    print("SOURCE: IDENTITY-CLEAN UNIQUE A2 DECISIONS")
    print("=" * 124)

    # ========================================================
    # A. BASELINE
    # ========================================================

    print()
    print("A. BASELINE")
    print("=" * 124)

    print(
        "Unique A2 decisions =",
        len(res)
    )

    print(
        "Winner rate = "
        f"{res['Winner'].mean()*100:.1f}%"
    )

    print()
    print("First deterioration:")
    print(
        res["FirstDeterioration"]
        .value_counts()
        .to_string()
    )

    # ========================================================
    # B. NORMAL BREATHING BEFORE DETERIORATION
    # ========================================================

    print()
    print("B. DEEPEST PRICE BREATHING WHILE EVIDENCE STILL INTACT")
    print("=" * 124)

    print("ALL:")
    print(
        describe(
            res["IntactBreathingMAE"]
        )
    )

    print()
    print("WINNERS:")
    print(
        describe(
            res.loc[
                res["Winner"],
                "IntactBreathingMAE"
            ]
        )
    )

    print()
    print("FAILURES:")
    print(
        describe(
            res.loc[
                ~res["Winner"],
                "IntactBreathingMAE"
            ]
        )
    )

    # ========================================================
    # C. DISTANCE WHEN FIRST DETERIORATION APPEARS
    # ========================================================

    print()
    print("C. PRICE DISTANCE AT FIRST REAL-TIME DETERIORATION")
    print("=" * 124)

    det = res[
        res["FirstDeterioration"]
        != "NONE"
    ]

    print("CLOSE distance:")
    print(
        describe(
            det["DistanceAtDetClose"]
        )
    )

    print()
    print("INTRADAY LOW distance:")
    print(
        describe(
            det["DistanceAtDetLow"]
        )
    )

    print()
    print("By first signal:")

    for signal in [
        "BIAS3",
        "MTM3",
        "DM",
    ]:

        g = det[
            det["FirstDeterioration"]
            == signal
        ]

        if len(g) == 0:
            continue

        print()
        print(signal)

        print(
            " Close | "
            + describe(
                g["DistanceAtDetClose"]
            )
        )

        print(
            " Low   | "
            + describe(
                g["DistanceAtDetLow"]
            )
        )

    # ========================================================
    # D. FALSE-STOP CONTROL
    #
    # How many eventual winners breathed below fixed price
    # levels BEFORE any bearish zero-cross?
    # ========================================================

    print()
    print("D. FALSE-STOP CONTROL — EVENTUAL WINNERS")
    print("=" * 124)

    winners = res[
        res["Winner"]
    ]

    for level in [-2, -3, -5]:

        n = (
            winners[
                "IntactBreathingMAE"
            ] <= level
        ).sum()

        rate = (
            n / len(winners) * 100
            if len(winners)
            else np.nan
        )

        print(
            f"Winner breathed <= {level}% "
            f"while evidence intact | "
            f"N={n:3} | "
            f"{rate:5.1f}%"
        )

    # ========================================================
    # E. NO-DETERIORATION GROUP
    # ========================================================

    print()
    print("E. NO BEARISH ZERO-CROSS WITHIN 10D")
    print("=" * 124)

    intact = res[
        res["FirstDeterioration"]
        == "NONE"
    ]

    print("N =", len(intact))

    if len(intact):

        print(
            "Winner rate = "
            f"{intact['Winner'].mean()*100:.1f}%"
        )

        print(
            "10D MAE | "
            + describe(
                intact["MAE10"]
            )
        )

        print(
            "FWD10   | "
            + describe(
                intact["FWD10"]
            )
        )

    # ========================================================
    # F. GUARDRAILS
    # ========================================================

    print()
    print("F. INTERPRETATION GUARDRAILS")
    print("=" * 124)

    print(
        "1. This study does NOT define a stop-loss."
    )

    print(
        "2. -2/-3/-5 are audit references only."
    )

    print(
        "3. First deterioration is a real-time observable "
        "state change, not future information."
    )

    print(
        "4. Breathing distance is descriptive evidence "
        "for a future prospective Risk Distance rule."
    )

    print(
        "5. Bias3/MTM3/D-M may trigger review or reduction; "
        "they do NOT automatically require full exit."
    )

    print()
    print("=" * 124)
    print("PROSPECTIVE RISK DISTANCE v0.1 COMPLETE")
    print(
        "QUESTION: WHERE DOES NORMAL BREATHING END "
        "AND THESIS DETERIORATION BEGIN?"
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
