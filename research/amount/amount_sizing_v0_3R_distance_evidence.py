import pandas as pd
import numpy as np
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

THRESHOLDS = [-2, -3, -5]

SCRIPT_VERSION = "AMOUNT SIZING v0.3R"
OUT_TXT = Path("reports/amount/amount_sizing_v0_3R_output.txt")
OUT_CSV = Path("reports/amount/amount_sizing_v0_3R_events.csv")

rows = []

# ============================================================
# BUILD EVENTS
# ============================================================

for ticker, f in FILES.items():

    df = pd.read_csv(f, header=[0,1], index_col=0)
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High", "Low", "Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    H, L, C = df["High"], df["Low"], df["Close"]

    # ========================================================
    # 1. SAME A2 / DUCK-BILL DEFINITION
    # ========================================================

    ma20 = C.rolling(20).mean()
    ma20_dir = ma20.diff()

    regime = pd.Series("SIDEWAYS", index=df.index)

    regime[
        (C > ma20) & (ma20_dir > 0)
    ] = "BULL"

    regime[
        (C < ma20) & (ma20_dir < 0)
    ] = "BEAR"

    sd20 = C.rolling(20).std()
    bw = 4 * sd20 / ma20
    q20 = bw.rolling(60).quantile(0.20)

    squeeze = bw <= q20

    expansion = (
        squeeze.shift(1)
        .fillna(False)
        .astype(bool)
        & (bw > bw.shift(1))
    )

    sideways_squeeze = (
        (regime == "SIDEWAYS") & squeeze
    )

    recent_origin = (
        sideways_squeeze.shift(1)
        .rolling(5)
        .max()
        .fillna(0)
        .astype(bool)
    )

    duck_up = (
        expansion
        & recent_origin
        & (C > ma20)
        & (ma20_dir > 0)
    )

    # ========================================================
    # 2. D-M
    # ========================================================

    ema12 = C.ewm(span=12, adjust=False).mean()
    ema26 = C.ewm(span=26, adjust=False).mean()

    dif = ema12 - ema26
    sig = dif.ewm(span=9, adjust=False).mean()

    dm = dif - sig
    dm_dir = dm.diff()

    dm_up = (
        ((dm > 0) & (dm_dir > 0))
        |
        ((dm > 0) & (dm.shift(1) <= 0))
    )

    dm_down0 = (
        (dm < 0)
        & (dm.shift(1) >= 0)
    )

    # ========================================================
    # 3. DI OSC — A2 CONFIRMATION ONLY
    # ========================================================

    up_move = H.diff()
    down_move = -L.diff()

    plus_dm = pd.Series(
        np.where(
            (up_move > down_move) & (up_move > 0),
            up_move, 0.0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (down_move > up_move) & (down_move > 0),
            down_move, 0.0
        ),
        index=df.index
    )

    tr = pd.concat([
        H-L,
        (H-C.shift()).abs(),
        (L-C.shift()).abs()
    ], axis=1).max(axis=1)

    atr14 = tr.ewm(alpha=1/14, adjust=False).mean()

    plus_di = (
        100 *
        plus_dm.ewm(alpha=1/14, adjust=False).mean()
        / atr14
    )

    minus_di = (
        100 *
        minus_dm.ewm(alpha=1/14, adjust=False).mean()
        / atr14
    )

    diosc = plus_di - minus_di
    di_dir = diosc.diff()

    di_up = (
        ((diosc > 0) & (di_dir > 0))
        |
        ((diosc > 0) & (diosc.shift(1) <= 0))
    )

    # ========================================================
    # 4. MTM3
    # ========================================================

    mtm3 = C - C.shift(3)
    mtm3_dir = mtm3.diff()

    mtm3_up = (
        ((mtm3 > 0) & (mtm3_dir > 0))
        |
        ((mtm3 > 0) & (mtm3.shift(1) <= 0))
    )

    mtm3_down0 = (
        (mtm3 < 0)
        & (mtm3.shift(1) >= 0)
    )

    # ========================================================
    # 5. BIAS3
    # ========================================================

    ma3 = C.rolling(3).mean()
    bias3 = (C / ma3 - 1) * 100

    bias3_down0 = (
        (bias3 < 0)
        & (bias3.shift(1) >= 0)
    )

    # ========================================================
    # 6. FIND REAL-TIME A2 T_ACTION
    # ========================================================

    for i in range(60, len(df)-25):

        if not duck_up.iloc[i]:
            continue

        dm_seen = False
        di_seen = False
        mtm_seen = False
        action_i = None

        for j in range(i+1, i+6):

            if dm_up.iloc[j]:
                dm_seen = True

            if di_up.iloc[j]:
                di_seen = True

            if mtm3_up.iloc[j]:
                mtm_seen = True

            if dm_seen and di_seen and mtm_seen:
                action_i = j
                break

        if action_i is None:
            continue

        entry = C.iloc[action_i]

        # ====================================================
        # 7. LOCKED DISTANCE TEST
        #
        # First threshold hit within next 10 trading days.
        # Evidence state is cumulative from T_action+1
        # through the threshold-hit day, inclusive.
        # ====================================================

        for threshold in THRESHOLDS:

            target = entry * (1 + threshold / 100)
            hit_i = None

            for k in range(action_i+1, action_i+11):
                if L.iloc[k] <= target:
                    hit_i = k
                    break

            if hit_i is None:
                continue

            window = slice(action_i+1, hit_i+1)

            bias_seen = bool(
                bias3_down0.iloc[window].any()
            )

            mtm_seen_down = bool(
                mtm3_down0.iloc[window].any()
            )

            dm_seen_down = bool(
                dm_down0.iloc[window].any()
            )

            # Locked mutually-exclusive hierarchy.
            if dm_seen_down:
                state = "DM_STATE_CHANGE"

            elif mtm_seen_down:
                state = "MOMENTUM_DETERIORATION"

            elif bias_seen:
                state = "EARLY_WARNING"

            else:
                state = "INTACT"

            hit_close = C.iloc[hit_i]

            post = {}

            for n in [1,3,5]:

                if hit_i+n < len(df):
                    post[n] = (
                        C.iloc[hit_i+n] / hit_close - 1
                    ) * 100
                else:
                    post[n] = np.nan

            final10 = (
                C.iloc[action_i+10] / entry - 1
            ) * 100

            rows.append({
                "Ticker": ticker,
                "T_action": df.index[action_i],
                "Threshold": threshold,
                "HitDate": df.index[hit_i],
                "HitLag": hit_i-action_i,
                "State": state,
                "Bias3DownSeen": bias_seen,
                "MTM3DownSeen": mtm_seen_down,
                "DMDownSeen": dm_seen_down,
                "Post1D": post[1],
                "Post3D": post[3],
                "Post5D": post[5],
                "Final10D_from_Taction": final10,
            })

ev = pd.DataFrame(rows)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
ev.to_csv(OUT_CSV, index=False)

# ============================================================
# REPORT
# ============================================================

def report():

    print("=" * 118)
    print("AMOUNT SIZING v0.3R — REPRODUCIBLE DISTANCE × EVIDENCE STATE")
    print("LOCKED DISTANCES: -2 / -3 / -5")
    print("CUMULATIVE STATE: T_ACTION -> FIRST DISTANCE HIT")
    print("NO ATTEMPT TO REPRODUCE OLD v0.3 FINGERPRINT")
    print("=" * 118)

    print()
    print("A. EVENT COUNTS")
    print("=" * 118)

    print(
        pd.crosstab(
            ev["Threshold"],
            ev["State"]
        ).to_string()
    )

    print()
    print("B. FINAL 10D OUTCOME BY DISTANCE × STATE")
    print("=" * 118)

    states = [
        "INTACT",
        "EARLY_WARNING",
        "MOMENTUM_DETERIORATION",
        "DM_STATE_CHANGE",
    ]

    for threshold in THRESHOLDS:

        print()
        print("THRESHOLD", threshold, "%")

        for state in states:

            g = ev[
                (ev.Threshold == threshold)
                & (ev.State == state)
            ]

            if not len(g):
                continue

            s = g["Final10D_from_Taction"]

            print(
                f"{state:24} | "
                f"N={len(g):3} | "
                f"mean={s.mean():6.2f}% | "
                f"median={s.median():6.2f}% | "
                f"loser={(s<0).mean()*100:5.1f}%"
            )

    print()
    print("C. POST-HIT CONTINUATION")
    print("=" * 118)

    for threshold in THRESHOLDS:

        print()
        print("THRESHOLD", threshold, "%")

        for state in states:

            g = ev[
                (ev.Threshold == threshold)
                & (ev.State == state)
            ]

            if not len(g):
                continue

            print()
            print(state, "| N =", len(g))

            for n in [1,3,5]:

                s = g[f"Post{n}D"].dropna()

                print(
                    f"{n}D | "
                    f"mean={s.mean():6.2f}% | "
                    f"median={s.median():6.2f}% | "
                    f"negative={(s<0).mean()*100:5.1f}%"
                )

    print()
    print("D. -3% WITHIN-STOCK CHECK")
    print("=" * 118)

    for ticker in FILES:

        print()
        print(ticker)

        for state in states:

            g = ev[
                (ev.Ticker == ticker)
                & (ev.Threshold == -3)
                & (ev.State == state)
            ]

            if not len(g):
                continue

            s = g["Final10D_from_Taction"]

            print(
                f"{state:24} | "
                f"N={len(g):2} | "
                f"mean={s.mean():6.2f}% | "
                f"median={s.median():6.2f}% | "
                f"loser={(s<0).mean()*100:5.1f}%"
            )

    print()
    print("E. REPRODUCIBILITY RECORD")
    print("=" * 118)

    print("SCRIPT =", __file__)
    print("EVENT CSV =", OUT_CSV)
    print("ROWS =", len(ev))

    print()
    print("=" * 118)
    print("AMOUNT SIZING v0.3R COMPLETE")
    print("DISTANCE DESCRIBES DAMAGE.")
    print("CUMULATIVE EVIDENCE STATE DESCRIBES THESIS HEALTH.")
    print("=" * 118)


with OUT_TXT.open("w", encoding="utf-8") as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT_TXT)
print(" ", OUT_CSV)
