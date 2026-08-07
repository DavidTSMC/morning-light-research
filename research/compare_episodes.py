"""
Morning Light Research
Episode Comparison Laboratory v0.1

Purpose
-------
Compare indicator behavior around selected market episodes.

Initial research lenses:
1. MTM3 / MTM10  -> momentum timing
2. OBV / MA3 / MA10 -> volume-flow confirmation
3. BBI -> structural confirmation

Research question
-----------------
Which indicators tend to:

    LEAD
        ↓
    CONFIRM
        ↓
    LAG

around a price turning point?

Principles
----------
Evidence first.
Descriptive evidence only.
No trading decisions.
No probability conclusion yet.
"""


print("🌅 Morning Light Research")
print("Episode Comparison Laboratory v0.1")
print("Lead → Confirm → Lag")
print("Research foundation created successfully.")

# ---------------------------------------------------------
# Episode 001
# 2330.TW | 2026-08-07 | Intraday reversal study
# ---------------------------------------------------------

episode = {
    "episode_id": "E001",
    "ticker": "2330.TW",
    "date": "2026-08-07",
    "timeframe": "5m",
    "start_time": "12:30",
    "turning_zone_start": "12:45",
    "turning_zone_end": "13:00",
    "end_time": "13:30",
    "research_type": "intraday_reversal",
}

print()
print("Episode loaded:")
for key, value in episode.items():
    print(f"{key:20s}: {value}")


# ============================================================
# STEP 3 — EPISODE EVIDENCE TABLE
# E001 | 2330.TW | 2026-08-07 | 5-minute
# Source: observed intraday snapshots
# Evidence only. Missing values remain missing.
# ============================================================

from pathlib import Path
import pandas as pd


evidence_rows = [
    # time, close, MTM3, MTM10, OBV, OBV_MA3, BBI
    ("12:30", 2365,   5,    0, -36722, -36823, 2364.11),
    ("12:35", 2365,   5,   -5, -36722, -36772, 2364.25),
    ("12:40", 2360,   0,  -10, -36878, -36774, 2363.84),
    ("12:45", 2355, -10,   -5, -37381, -36994, 2362.43),
    ("12:50", 2355, -10,   -5, -37381, -37213, 2360.96),
    ("12:55", 2360,   0,    0, -37052, -37271, 2360.55),
    ("13:00", 2355,   0,  -10, -37206, -37213, 2359.54),
    ("13:05", 2370,  15,   10, -36050, -36769, 2361.39),
    ("13:10", 2370,  10,   10, -36050, -36435, 2363.06),
    ("13:15", 2370,  15,   10, -36050, -36050, 2365.21),
    ("13:20", 2370,   0, None, -36050, -36050, 2365.83),
    ("13:25", 2375,   5, None, -35269, -35790, 2367.60),
    ("13:30", 2370,   0, None, -38955, -36758, 2367.96),
]


columns = [
    "time",
    "close",
    "MTM3",
    "MTM10",
    "OBV",
    "OBV_MA3",
    "BBI",
]

evidence = pd.DataFrame(evidence_rows, columns=columns)


# ------------------------------------------------------------
# Mark each observation relative to the known turning zone.
# ------------------------------------------------------------

def classify_role(time_text):
    if time_text < "12:45":
        return "LEAD"
    elif time_text <= "13:00":
        return "TURNING_ZONE"
    else:
        return "CONFIRM_OR_LAG"


evidence["role"] = evidence["time"].apply(classify_role)


# ------------------------------------------------------------
# Episode identity
# ------------------------------------------------------------

evidence.insert(0, "episode_id", episode["episode_id"])
evidence.insert(1, "ticker", episode["ticker"])
evidence.insert(2, "date", episode["date"])
evidence.insert(3, "timeframe", episode["timeframe"])









# ------------------------------------------------------------
# Save descriptive evidence
# ------------------------------------------------------------

report_folder = Path("reports")
report_folder.mkdir(exist_ok=True)

output_file = report_folder / "episode_E001_evidence.csv"

evidence.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
)


print()
print("=" * 72)
print("E001 — EPISODE EVIDENCE TABLE")
print("=" * 72)
print(evidence.to_string(index=False))

print()
print(f"Rows captured : {len(evidence)}")
print(f"Saved to      : {output_file}")
print("Missing values: intentionally preserved — no guessing.")
print("=" * 72)


# ============================================================
# STEP 3C — DESCRIPTIVE LEAD / CONFIRM / LAG ANALYSIS
# No prediction. No trading decision.
# ============================================================

def first_positive_after_negative(df, column):
    """
    Find the first bar where an indicator becomes positive
    after the immediately preceding valid observation was negative.
    """
    series = df[["time", column]].dropna().reset_index(drop=True)

    for i in range(1, len(series)):
        previous = series.loc[i - 1, column]
        current = series.loc[i, column]

        if previous < 0 and current > 0:
            return series.loc[i, "time"]

    return None


def first_positive_after_negative_or_zero_bridge(df, column):
    """
    Find the first positive observation after the indicator
    has previously been negative.

    Zero values between the negative observation and the
    first positive observation are allowed.

    Example:
        -10 -> 0 -> 0 -> +15

    This is descriptive evidence only.
    """

    series = df[["time", column]].dropna().reset_index(drop=True)

    seen_negative = False

    for i in range(len(series)):
        current = series.loc[i, column]

        if current < 0:
            seen_negative = True

        elif current > 0 and seen_negative:
            return series.loc[i, "time"]

    return None





def first_obv_above_ma3_after_below(df):
    """
    Find the first bar where OBV moves above OBV_MA3
    after previously being below it.
    """
    temp = df[
        ["time", "OBV", "OBV_MA3"]
    ].dropna().reset_index(drop=True)

    for i in range(1, len(temp)):
        previous_diff = (
            temp.loc[i - 1, "OBV"]
            - temp.loc[i - 1, "OBV_MA3"]
        )

        current_diff = (
            temp.loc[i, "OBV"]
            - temp.loc[i, "OBV_MA3"]
        )

        if previous_diff < 0 and current_diff > 0:
            return temp.loc[i, "time"]

    return None


def first_bbi_upturn(df):
    """
    First observation where BBI rises versus the prior bar
    after a declining observation.
    """
    temp = df[["time", "BBI"]].dropna().reset_index(drop=True)

    change = temp["BBI"].diff()

    for i in range(2, len(temp)):
        if change.iloc[i - 1] < 0 and change.iloc[i] > 0:
            return temp.loc[i, "time"]

    return None


mtm3_cross = first_positive_after_negative(evidence, "MTM3")
mtm3_zero_bridge = first_positive_after_negative_or_zero_bridge(
    evidence, "MTM3"
)    

mtm10_cross = first_positive_after_negative(evidence, "MTM10")
obv_cross = first_obv_above_ma3_after_below(evidence)
bbi_turn = first_bbi_upturn(evidence)


print()
print("=" * 72)
print("E001 — FIRST DESCRIPTIVE TIMING EVENTS")
print("=" * 72)

print(f"Turning zone       : 12:45 -> 13:00")
print(f"MTM3 first > 0     : {mtm3_cross}")
print(f"MTM3 zero-bridge   : {mtm3_zero_bridge}")
print(f"MTM10 first > 0    : {mtm10_cross}")
print(f"OBV > OBV_MA3      : {obv_cross}")
print(f"BBI first upturn   : {bbi_turn}")

print()
print("Interpretation:")
print("Times are descriptive observations only.")
print("Earlier does not automatically mean better.")
print("Repeated episodes are required before assigning roles.")
print("=" * 72)





