import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

EPFILE = Path(
    "reports/amount/prospective_risk_distance_v0_2R_bias_landslide.csv"
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
    "reports/amount/prospective_risk_distance_v0_3_bias20_timing.txt"
)

OUT_CSV = Path(
    "reports/amount/prospective_risk_distance_v0_3_bias20_timing.csv"
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

    for c in ["Low", "Close"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    C = df["Close"]
    L = df["Low"]

    # Same definitions as v0.2R
    ma10 = C.rolling(10).mean()
    ma20 = C.rolling(20).mean()

    bias10 = (C / ma10 - 1) * 100
    bias20 = (C / ma20 - 1) * 100

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

        # Need enough future data for:
        # 10D episode + 5D after B20
        if loc + 15 >= len(df):
            continue

        entry = C.iloc[loc]

        # ====================================================
        # RECONSTRUCT FIRST B10 / B20 BEARISH ZERO-CROSS
        # WITHIN ORIGINAL 10D RESEARCH HORIZON
        # ====================================================

        b10 = None
        b20 = None

        for j in range(loc+1, loc+11):

            if (
                b10 is None
                and bias10.iloc[j] < 0
                and bias10.iloc[j-1] >= 0
            ):
                b10 = j

            if (
                b20 is None
                and bias20.iloc[j] < 0
                and bias20.iloc[j-1] >= 0
            ):
                b20 = j

        if b20 is None:
            continue

        # ====================================================
        # DAMAGE AT B20
        # ====================================================

        b20_close_dist = (
            C.iloc[b20] / entry - 1
        ) * 100

        b20_low_dist = (
            L.iloc[b20] / entry - 1
        ) * 100

        # Original episode MAE through T_action +10D
        end10 = loc + 10

        episode_low = L.iloc[
            loc+1:end10+1
        ].min()

        mae10 = (
            episode_low / entry - 1
        ) * 100

        # ====================================================
        # HAD THE 10D LOCAL LOW ALREADY OCCURRED BY B20?
        # ====================================================

        pre_b20_low = L.iloc[
            loc+1:b20+1
        ].min()

        post_b20_low = L.iloc[
            b20+1:end10+1
        ].min() if b20 < end10 else np.nan

        low_already_seen = (
            pre_b20_low <= episode_low + 1e-12
        )

        # Fraction of eventual downside already realized.
        # Use absolute magnitudes only when both are negative.
        if (
            mae10 < 0
            and b20_low_dist < 0
        ):
            damage_fraction = min(
                abs(b20_low_dist)
                / abs(mae10),
                1.0
            ) * 100
        else:
            damage_fraction = np.nan

        # ====================================================
        # WHAT HAPPENS AFTER B20?
        # Close-to-close return from B20 trigger close.
        # ====================================================

        def post_return(days):

            k = b20 + days

            if k >= len(C):
                return np.nan

            return (
                C.iloc[k]
                / C.iloc[b20] - 1
            ) * 100

        post1 = post_return(1)
        post3 = post_return(3)
        post5 = post_return(5)

        # ====================================================
        # BOUNCE TEST
        #
        # Did price close above B20 trigger close afterward?
        # ====================================================

        bounce1 = (
            post1 > 0
            if not np.isnan(post1)
            else np.nan
        )

        bounce3 = (
            post3 > 0
            if not np.isnan(post3)
            else np.nan
        )

        bounce5 = (
            post5 > 0
            if not np.isnan(post5)
            else np.nan
        )

        # ====================================================
        # B10 -> B20 COST OF WAITING
        # ====================================================

        if b10 is not None and b10 <= b20:

            lag10to20 = b20 - b10

            b10_close_dist = (
                C.iloc[b10] / entry - 1
            ) * 100

            b10_low_dist = (
                L.iloc[b10] / entry - 1
            ) * 100

            extra_close_damage = (
                b20_close_dist
                - b10_close_dist
            )

            extra_low_damage = (
                b20_low_dist
                - b10_low_dist
            )

        else:

            lag10to20 = np.nan
            b10_close_dist = np.nan
            b10_low_dist = np.nan
            extra_close_damage = np.nan
            extra_low_damage = np.nan

        rows.append({
            "Ticker": ticker,
            "T_action": t,
            "Winner": bool(e["Winner"]),
            "FWD10": e["FWD10"],

            "B10Date":
                df.index[b10]
                if b10 is not None
                else pd.NaT,

            "B20Date":
                df.index[b20],

            "B10toB20Lag":
                lag10to20,

            "B10CloseDist":
                b10_close_dist,

            "B20CloseDist":
                b20_close_dist,

            "ExtraCloseDamage10to20":
                extra_close_damage,

            "B10LowDist":
                b10_low_dist,

            "B20LowDist":
                b20_low_dist,

            "ExtraLowDamage10to20":
                extra_low_damage,

            "MAE10":
                mae10,

            "DamageAlreadyRealizedPct":
                damage_fraction,

            "LowAlreadySeenByB20":
                low_already_seen,

            "PostB20_1D":
                post1,

            "PostB20_3D":
                post3,

            "PostB20_5D":
                post5,

            "Bounce1D":
                bounce1,

            "Bounce3D":
                bounce3,

            "Bounce5D":
                bounce5,
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


def stats(s):

    s = pd.to_numeric(
        s,
        errors="coerce"
    ).dropna()

    if len(s) == 0:
        return "N=0"

    return (
        f"N={len(s):3} | "
        f"mean={s.mean():6.2f} | "
        f"median={s.median():6.2f} | "
        f"P25={s.quantile(.25):6.2f} | "
        f"P75={s.quantile(.75):6.2f}"
    )


def rate(s):

    s = s.dropna()

    if len(s) == 0:
        return np.nan

    return s.astype(bool).mean() * 100


def report():

    print("=" * 126)
    print("PROSPECTIVE RISK DISTANCE v0.3")
    print("BIAS20 LATE-WARNING / REBOUND AUDIT")
    print("QUESTION: IS BIAS20 AN ACTION SIGNAL OR A DISASTER INSPECTOR?")
    print("=" * 126)

    print()
    print("A. BIAS20 SAMPLE")
    print("=" * 126)

    print("Bias20 trigger cases =", len(res))

    print(
        "Winners =",
        int(res["Winner"].sum())
    )

    print(
        "Failures =",
        int((~res["Winner"]).sum())
    )

    print(
        "Winner rate = "
        f"{res['Winner'].mean()*100:.1f}%"
    )

    # ========================================================
    # B. DAMAGE ALREADY REALIZED
    # ========================================================

    print()
    print("B. HOW MUCH DAMAGE HAD ALREADY OCCURRED AT BIAS20?")
    print("=" * 126)

    print(
        "B20 close distance | "
        + stats(res["B20CloseDist"])
    )

    print(
        "B20 low distance   | "
        + stats(res["B20LowDist"])
    )

    print(
        "10D MAE            | "
        + stats(res["MAE10"])
    )

    print(
        "Damage already realized % | "
        + stats(res["DamageAlreadyRealizedPct"])
    )

    print()
    print(
        "10D local low already seen by B20 = "
        f"{rate(res['LowAlreadySeenByB20']):.1f}%"
    )

    # ========================================================
    # C. B10 -> B20 WAITING COST
    # ========================================================

    print()
    print("C. COST OF WAITING FROM BIAS10 TO BIAS20")
    print("=" * 126)

    both = res[
        res["B10toB20Lag"].notna()
    ]

    print(
        "Cases with ordered B10 -> B20 =",
        len(both)
    )

    print(
        "Lag days | "
        + stats(both["B10toB20Lag"])
    )

    print(
        "Additional CLOSE move | "
        + stats(
            both["ExtraCloseDamage10to20"]
        )
    )

    print(
        "Additional LOW move   | "
        + stats(
            both["ExtraLowDamage10to20"]
        )
    )

    # ========================================================
    # D. POST-B20 PATH
    # ========================================================

    print()
    print("D. WHAT HAPPENS AFTER BIAS20?")
    print("=" * 126)

    for d in [1, 3, 5]:

        print(
            f"{d}D return | "
            + stats(
                res[f"PostB20_{d}D"]
            )
        )

        print(
            f"{d}D bounce rate = "
            f"{rate(res[f'Bounce{d}D']):.1f}%"
        )

    # ========================================================
    # E. WINNER vs FAILURE AFTER B20
    # ========================================================

    print()
    print("E. POST-B20 — WINNERS vs FAILURES")
    print("=" * 126)

    for label, g in [
        ("WINNERS", res[res["Winner"]]),
        ("FAILURES", res[~res["Winner"]]),
    ]:

        print()
        print(label)

        for d in [1, 3, 5]:

            print(
                f" {d}D | "
                + stats(
                    g[f"PostB20_{d}D"]
                )
                + " | bounce="
                + f"{rate(g[f'Bounce{d}D']):.1f}%"
            )

    # ========================================================
    # F. INTERPRETATION
    # ========================================================

    print()
    print("F. INTERPRETATION GUARDRAIL")
    print("=" * 126)

    print(
        "1. Bias20 discrimination was established in v0.2R; "
        "this test asks whether that information arrives in time."
    )

    print(
        "2. A high damage-already-realized percentage suggests "
        "diagnostic value may exceed action value."
    )

    print(
        "3. A high post-B20 bounce rate warns against treating "
        "Bias20 as an automatic exit."
    )

    print(
        "4. Continued negative 1D/3D/5D returns after B20 would "
        "support additional action value."
    )

    print(
        "5. No Bias horizon receives production authority "
        "from this test alone."
    )

    print()
    print("=" * 126)
    print("PROSPECTIVE RISK DISTANCE v0.3 COMPLETE")
    print(
        "EARLY ENOUGH TO ACT. RELIABLE ENOUGH TO TRUST."
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
