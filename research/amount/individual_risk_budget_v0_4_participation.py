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

OUT_TXT = Path(
    "reports/amount/individual_risk_budget_v0_4_participation.txt"
)
OUT_CSV = Path(
    "reports/amount/individual_risk_budget_v0_4_participation.csv"
)

# Scenario lenses only — NOT production parameters.
BUDGETS = [0.25, 0.50, 1.00]

# Geometry lenses only.
DISTANCES = [2.0, 3.0, 5.0]

rows = []

for ticker, f in FILES.items():

    df = pd.read_csv(f, header=[0,1], index_col=0)
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High","Low","Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    H, L, C = df["High"], df["Low"], df["Close"]

    # ========================================================
    # SAME LOCKED A2 FORMATION
    # ========================================================

    ma20 = C.rolling(20).mean()
    ma20_dir = ma20.diff()

    regime = pd.Series("SIDEWAYS", index=df.index)
    regime[(C > ma20) & (ma20_dir > 0)] = "BULL"
    regime[(C < ma20) & (ma20_dir < 0)] = "BEAR"

    sd20 = C.rolling(20).std()
    bw = 4 * sd20 / ma20
    q20 = bw.rolling(60).quantile(0.20)

    squeeze = bw <= q20

    expansion = (
        squeeze.shift(1).fillna(False).astype(bool)
        & (bw > bw.shift(1))
    )

    sideways_squeeze = (
        (regime == "SIDEWAYS")
        & squeeze
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

    # D-M
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

    # DI OSC
    up_move = H.diff()
    down_move = -L.diff()

    plus_dm = pd.Series(
        np.where(
            (up_move > down_move) & (up_move > 0),
            up_move,
            0.0
        ),
        index=df.index
    )

    minus_dm = pd.Series(
        np.where(
            (down_move > up_move) & (down_move > 0),
            down_move,
            0.0
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
        100
        * plus_dm.ewm(alpha=1/14, adjust=False).mean()
        / atr14
    )

    minus_di = (
        100
        * minus_dm.ewm(alpha=1/14, adjust=False).mean()
        / atr14
    )

    diosc = plus_di - minus_di
    di_dir = diosc.diff()

    di_up = (
        ((diosc > 0) & (di_dir > 0))
        |
        ((diosc > 0) & (diosc.shift(1) <= 0))
    )

    # MTM3
    mtm3 = C - C.shift(3)
    mtm3_dir = mtm3.diff()

    mtm3_up = (
        ((mtm3 > 0) & (mtm3_dir > 0))
        |
        ((mtm3 > 0) & (mtm3.shift(1) <= 0))
    )

    # ========================================================
    # ONE ROW PER A2 EPISODE
    # ========================================================

    for i in range(60, len(df)-15):

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

        fwd10 = (
            C.iloc[action_i+10] / entry - 1
        ) * 100

        rows.append({
            "Ticker": ticker,
            "T_action": df.index[action_i],
            "FWD10": fwd10,
            "Winner": fwd10 > 0,
        })

ev = pd.DataFrame(rows)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
ev.to_csv(OUT_CSV, index=False)

# ============================================================
# REPORT
# ============================================================

def report():

    print("=" * 120)
    print("INDIVIDUAL RISK BUDGET v0.4 — PARTICIPATION EFFICIENCY")
    print("ENOUGH TO MATTER × SMALL ENOUGH TO SURVIVE")
    print("ONE ROW PER A2 EPISODE | NO DISTANCE-HIT SELECTION")
    print("=" * 120)

    print()
    print("A. A2 OUTCOME BASELINE")
    print("=" * 120)

    print("A2 episodes =", len(ev))
    print("10D winners =", int(ev.Winner.sum()))
    print(
        "10D win rate = "
        f"{ev.Winner.mean()*100:.1f}%"
    )
    print(
        "Mean FWD10 = "
        f"{ev.FWD10.mean():.2f}%"
    )
    print(
        "Median FWD10 = "
        f"{ev.FWD10.median():.2f}%"
    )

    winners = ev[ev.Winner].copy()

    print()
    print("B. WINNER PARTICIPATION BASELINE")
    print("=" * 120)

    print("Winner N =", len(winners))
    print(
        "Winner mean FWD10 = "
        f"{winners.FWD10.mean():.2f}%"
    )
    print(
        "Winner median FWD10 = "
        f"{winners.FWD10.median():.2f}%"
    )

    # ========================================================
    # C. PORTFOLIO CONTRIBUTION
    #
    # Raw position = Budget / Distance
    #
    # Portfolio contribution =
    # position fraction × stock return
    # ========================================================

    print()
    print("C. TYPICAL WINNER CONTRIBUTION BY BUDGET × DISTANCE")
    print("=" * 120)

    winner_mean = winners.FWD10.mean()
    winner_median = winners.FWD10.median()

    for b in BUDGETS:

        print()
        print(f"RISK BUDGET = {b:.2f}%")

        for d in DISTANCES:

            position_pct = (
                b / d * 100
            )

            mean_contribution = (
                position_pct / 100
                * winner_mean
            )

            median_contribution = (
                position_pct / 100
                * winner_median
            )

            print(
                f"Distance={d:3.1f}% | "
                f"Raw position={position_pct:6.2f}% | "
                f"mean winner contribution={mean_contribution:6.3f}% | "
                f"median winner contribution={median_contribution:6.3f}%"
            )

    # ========================================================
    # D. PARTICIPATION EFFICIENCY
    #
    # contribution / budget
    #
    # If sizing is perfectly linear, this should depend on
    # payoff relative to distance, NOT on budget itself.
    # ========================================================

    print()
    print("D. CONTRIBUTION PER 1 UNIT OF RISK BUDGET")
    print("=" * 120)

    for d in DISTANCES:

        print()
        print(f"RISK DISTANCE = {d:.1f}%")

        for b in BUDGETS:

            position_pct = (
                b / d * 100
            )

            contribution = (
                position_pct / 100
                * winner_mean
            )

            efficiency = (
                contribution / b
            )

            print(
                f"Budget={b:4.2f}% | "
                f"contribution={contribution:6.3f}% | "
                f"contribution/budget={efficiency:6.3f}"
            )

    # ========================================================
    # E. WINNERS NEEDED TO REPAIR ONE FULL RISK UNIT
    #
    # One fully consumed budget loses b%.
    # Typical winner contributes position × winner return.
    # ========================================================

    print()
    print("E. TYPICAL WINNERS NEEDED TO REPAIR ONE FULL FAILURE")
    print("=" * 120)

    for d in DISTANCES:

        print()
        print(f"RISK DISTANCE = {d:.1f}%")

        for b in BUDGETS:

            position_pct = (
                b / d * 100
            )

            contribution = (
                position_pct / 100
                * winner_mean
            )

            needed = (
                b / contribution
                if contribution > 0
                else np.nan
            )

            print(
                f"Budget={b:4.2f}% | "
                f"typical winner contribution={contribution:6.3f}% | "
                f"winners_to_repair={needed:5.2f}"
            )

    # ========================================================
    # F. LINEARITY CHECK
    # ========================================================

    print()
    print("F. LINEARITY CHECK")
    print("=" * 120)

    print(
        "If contribution/budget and winners_to_repair "
        "remain unchanged across 0.25/0.50/1.00 at the same "
        "distance, then Risk Budget does NOT create edge."
    )

    print()
    print(
        "It only scales the amplitude of an existing edge."
    )

    print()
    print(
        "In that case, Base Risk Budget should be chosen from "
        "portfolio damage capacity, not return optimization."
    )

    print()
    print("=" * 120)
    print("INDIVIDUAL RISK BUDGET v0.4 COMPLETE")
    print("ENOUGH TO MATTER. SMALL ENOUGH TO SURVIVE.")
    print("FLEXIBLE ENOUGH TO RESPOND.")
    print("=" * 120)


OUT_TXT.parent.mkdir(parents=True, exist_ok=True)

with OUT_TXT.open("w", encoding="utf-8") as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT_TXT)
print(" ", OUT_CSV)
