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

OUT_TXT = Path("reports/amount/risk_budget_v0_1_simultaneous_a2.txt")
OUT_CSV = Path("reports/amount/risk_budget_v0_1_daily_exposure.csv")

ACTIVE_DAYS = 10

events = []
price_data = {}

# ============================================================
# 1. REBUILD SAME LOCKED A2 READY EVENTS
# ============================================================

for ticker, f in FILES.items():

    df = pd.read_csv(f, header=[0,1], index_col=0)
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High","Low","Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    H, L, C = df["High"], df["Low"], df["Close"]
    price_data[ticker] = df.copy()

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

    # MTM3
    mtm3 = C - C.shift(3)
    mtm3_dir = mtm3.diff()

    mtm3_up = (
        ((mtm3 > 0) & (mtm3_dir > 0))
        |
        ((mtm3 > 0) & (mtm3.shift(1) <= 0))
    )

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

        end_i = min(
            action_i + ACTIVE_DAYS - 1,
            len(df)-1
        )

        events.append({
            "Ticker": ticker,
            "T_action": df.index[action_i],
            "ActiveEnd": df.index[end_i],
            "Entry": C.iloc[action_i],
        })

events = pd.DataFrame(events)

# ============================================================
# 2. COMMON TRADING CALENDAR
# ============================================================

calendar = sorted(
    set().union(
        *[set(df.index) for df in price_data.values()]
    )
)

daily_rows = []

for date in calendar:

    active = events[
        (events["T_action"] <= date)
        & (events["ActiveEnd"] >= date)
    ]

    tickers = sorted(active["Ticker"].unique())

    daily_rows.append({
        "Date": date,
        "ActiveCount": len(tickers),
        "ActiveTickers": ",".join(tickers),
    })

daily = pd.DataFrame(daily_rows)

# ============================================================
# 3. NEXT-5D JOINT DAMAGE FROM EACH CALENDAR DAY
#
# For each active ticker:
# measure worst Low over its next 5 trading observations
# relative to that day's Close.
#
# JointDamageCount:
# number of active tickers reaching <= -3% MAE.
# ============================================================

joint_damage = []

for _, row in daily.iterrows():

    date = row["Date"]

    tickers = (
        row["ActiveTickers"].split(",")
        if row["ActiveTickers"]
        else []
    )

    damaged = 0
    valid = 0

    for ticker in tickers:

        df = price_data[ticker]

        if date not in df.index:
            continue

        loc = df.index.get_loc(date)

        if not isinstance(loc, (int, np.integer)):
            continue

        if loc + 5 >= len(df):
            continue

        close0 = df["Close"].iloc[loc]

        low5 = df["Low"].iloc[
            loc+1:loc+6
        ].min()

        mae5 = (
            low5 / close0 - 1
        ) * 100

        valid += 1

        if mae5 <= -3:
            damaged += 1

    joint_damage.append({
        "Date": date,
        "ValidActive": valid,
        "JointDamageCount": damaged,
        "AnyDamage": damaged >= 1,
        "MultiDamage": damaged >= 2,
    })

joint = pd.DataFrame(joint_damage)

daily = daily.merge(
    joint,
    on="Date",
    how="left"
)

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
daily.to_csv(OUT_CSV, index=False)

# ============================================================
# REPORT
# ============================================================

def report():

    print("=" * 118)
    print("RISK BUDGET v0.1 — SIMULTANEOUS A2 EXPOSURE MAP")
    print(f"A2 ACTIVE WINDOW = {ACTIVE_DAYS} TRADING DAYS FROM T_ACTION")
    print("NO CORRELATION OR POSITION-SIZE ASSUMPTIONS")
    print("=" * 118)

    print()
    print("A. A2 EVENT COUNTS")
    print("=" * 118)

    print("TOTAL A2 EVENTS =", len(events))

    print()
    print(
        events.groupby("Ticker")
        .size()
        .to_string()
    )

    print()
    print("B. SIMULTANEOUS ACTIVE EXPOSURE")
    print("=" * 118)

    counts = (
        daily["ActiveCount"]
        .value_counts()
        .sort_index()
    )

    for n, days in counts.items():

        pct = (
            days / len(daily) * 100
        )

        print(
            f"{n} active | "
            f"days={days:4} | "
            f"{pct:5.1f}%"
        )

    print()
    print(
        "MAX SIMULTANEOUS A2 =",
        int(daily.ActiveCount.max())
    )

    print()
    print("C. WHEN >=2 A2 ARE ACTIVE")
    print("=" * 118)

    multi = daily[
        daily.ActiveCount >= 2
    ]

    print("Days =", len(multi))

    if len(multi):

        print(
            "Any next-5D <= -3% damage = "
            f"{multi.AnyDamage.mean()*100:5.1f}%"
        )

        print(
            "Two-or-more jointly damaged = "
            f"{multi.MultiDamage.mean()*100:5.1f}%"
        )

    print()
    print("D. DAMAGE RATE BY NUMBER OF ACTIVE A2")
    print("=" * 118)

    for n in sorted(
        daily.ActiveCount.unique()
    ):

        if n == 0:
            continue

        g = daily[
            daily.ActiveCount == n
        ]

        print(
            f"{n} active | "
            f"Ndays={len(g):4} | "
            f"any_damage={g.AnyDamage.mean()*100:5.1f}% | "
            f"multi_damage={g.MultiDamage.mean()*100:5.1f}%"
        )

    print()
    print("E. MOST COMMON MULTI-A2 COMBINATIONS")
    print("=" * 118)

    combos = (
        multi["ActiveTickers"]
        .value_counts()
        .head(15)
    )

    if len(combos):
        print(combos.to_string())
    else:
        print("No multi-A2 days.")

    print()
    print("F. REPRODUCIBILITY RECORD")
    print("=" * 118)

    print("SCRIPT =", __file__)
    print("DAILY CSV =", OUT_CSV)
    print("CALENDAR DAYS =", len(daily))

    print()
    print("=" * 118)
    print("RISK BUDGET v0.1 COMPLETE")
    print("QUESTION: HOW OFTEN CAN MULTIPLE A2 THESES BE HURT TOGETHER?")
    print("=" * 118)


OUT_TXT.parent.mkdir(parents=True, exist_ok=True)

with OUT_TXT.open("w", encoding="utf-8") as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT_TXT)
print(" ", OUT_CSV)
