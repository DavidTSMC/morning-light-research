import pandas as pd
import numpy as np

FILES = {
    "2882": "data/raw/2882_TW_5Y.csv",
    "2330": "data/raw/2330_TW_5Y.csv",
    "2454": "data/raw/2454_TW_5Y.csv",
    "0050": "data/raw/0050_TW_5Y.csv",
    "2603": "data/raw/2603_TW_5Y.csv",
    "2382": "data/raw/2382_TW_5Y.csv",
}

THRESHOLDS = [-2, -3, -5]

EXPECTED = {
    -2: {
        "DM_EVENT": 10,
        "EVIDENCE_INTACT": 9,
        "MULTI_DETERIORATION": 51,
        "ONE_WARNING": 13,
    },
    -3: {
        "DM_EVENT": 15,
        "EVIDENCE_INTACT": 0,
        "MULTI_DETERIORATION": 42,
        "ONE_WARNING": 7,
    },
    -5: {
        "DM_EVENT": 17,
        "EVIDENCE_INTACT": 0,
        "MULTI_DETERIORATION": 25,
        "ONE_WARNING": 1,
    },
}

rows = []

for ticker, f in FILES.items():

    df = pd.read_csv(f, header=[0,1], index_col=0)
    df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)

    for c in ["High", "Low", "Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    H, L, C = df["High"], df["Low"], df["Close"]

    # ========================================================
    # SAME A2 READY DEFINITION
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

    # ========================================================
    # D-M
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

    dm_warning = dm.diff() < 0

    # ========================================================
    # DI OSC
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

    di_warning = di_dir < 0

    # ========================================================
    # MTM3
    # ========================================================

    mtm = C - C.shift(3)
    mtm_dir = mtm.diff()

    mtm_up = (
        ((mtm > 0) & (mtm_dir > 0))
        |
        ((mtm > 0) & (mtm.shift(1) <= 0))
    )

    mtm_warning = mtm_dir < 0

    # ========================================================
    # BIAS3
    # ========================================================

    ma3 = C.rolling(3).mean()
    bias3 = (C / ma3 - 1) * 100
    bias_warning = bias3.diff() < 0

    # ========================================================
    # FIND A2 T_ACTION
    # ========================================================

    for i in range(60, len(df)-20):

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

            if mtm_up.iloc[j]:
                mtm_seen = True

            if dm_seen and di_seen and mtm_seen:
                action_i = j
                break

        if action_i is None:
            continue

        entry = C.iloc[action_i]

        # ----------------------------------------------------
        # For each locked distance:
        # find FIRST future day whose intraday Low reaches it.
        # ----------------------------------------------------

        for threshold in THRESHOLDS:

            hit_i = None
            target = entry * (1 + threshold / 100)

            for k in range(action_i+1, action_i+11):
                if L.iloc[k] <= target:
                    hit_i = k
                    break

            if hit_i is None:
                continue

            # ------------------------------------------------
            # Candidate reconstruction of v0.3 evidence state
            # AT THE DISTANCE-HIT DAY.
            #
            # Priority:
            # DM_EVENT > MULTI > ONE_WARNING > INTACT
            # ------------------------------------------------

            if dm_down0.iloc[hit_i]:
                state = "DM_EVENT"

            else:
                warnings = int(bias_warning.iloc[hit_i])
                warnings += int(mtm_warning.iloc[hit_i])
                warnings += int(di_warning.iloc[hit_i])
                warnings += int(dm_warning.iloc[hit_i])

                if warnings >= 2:
                    state = "MULTI_DETERIORATION"
                elif warnings == 1:
                    state = "ONE_WARNING"
                else:
                    state = "EVIDENCE_INTACT"

            rows.append({
                "Ticker": ticker,
                "Threshold": threshold,
                "State": state,
            })

ev = pd.DataFrame(rows)

actual = {}

print()
print("=" * 118)
print("AMOUNT SIZING v0.3 — DEFINITION AUDIT")
print("RECONSTRUCTION MUST MATCH THE LOCKED EVENT-COUNT FINGERPRINT")
print("=" * 118)

for threshold in THRESHOLDS:

    print()
    print("THRESHOLD", threshold, "%")
    print("-" * 70)

    g = ev[ev.Threshold == threshold]

    actual[threshold] = {}

    for state in [
        "DM_EVENT",
        "EVIDENCE_INTACT",
        "MULTI_DETERIORATION",
        "ONE_WARNING",
    ]:

        n = int((g.State == state).sum())
        actual[threshold][state] = n

        expected = EXPECTED[threshold][state]

        mark = "OK" if n == expected else "MISMATCH"

        print(
            f"{state:20} | "
            f"actual={n:3} | "
            f"expected={expected:3} | "
            f"{mark}"
        )

# ============================================================
# STRICT FINGERPRINT TEST
# ========================================================

match = actual == EXPECTED

print()
print("=" * 118)

if match:
    print("FINGERPRINT MATCH = PASS")
    print("v0.3 DEFINITION REPRODUCED.")
else:
    print("FINGERPRINT MATCH = FAIL")
    print("DO NOT PROCEED TO v0.4.")
    print("NO PARAMETERS OR DEFINITIONS SHOULD BE TUNED TO FORCE A MATCH.")

print("=" * 118)
