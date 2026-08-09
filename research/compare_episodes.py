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
episode_E001 = {
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

episode_E002 = {
    "episode_id": "E002",
    "ticker": "0050.TW",
    "date": "2026-08-07",
    "timeframe": "5m",
    "start_time": "12:30",
    "turning_zone_start": "12:40",
    "turning_zone_end": "13:00",
    "end_time": "13:30",
    "research_type": "intraday_reversal",
}

episode_E003 = {
    "episode_id": "E003",
    "ticker": "2454.TW",
    "date": "2026-08-07",
    "timeframe": "5m",
    "start_time": "12:20",
    "turning_zone_start": "12:50",
    "turning_zone_end": "13:05",
    "end_time": "13:30",
    "research_type": "intraday_reversal",
}

episode_E004 = {
    "episode_id": "E004",
    "ticker": "XAUUSD",
    "date": "2026-08-07",
    "timeframe": "5m",
    "start_time": "19:15",
    "turning_zone_start": "20:15",
    "turning_zone_end": "20:30",
    "end_time": "20:45",
    "research_type": "intraday_reversal",
}


# Select episode for current research run
episode = episode_E004


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

# ------------------------------------------------------------
# E002 - 0050.TW - 2026-08-07 - 5-minute evidence
# ------------------------------------------------------------

evidence_rows_E002 = [
    # time, close, MTM3, MTM10, OBV, OBV_MA3, BBI
    ("12:30", 102.60,  0.00, -0.03, -367848, -367959, 102.62),
    ("12:35", 102.60,  0.10, -0.04, -367848, -367848, 102.63),
    ("12:40", 102.45, -0.15, -0.05, -368582, -368093, 102.60),
    ("12:45", 102.25, -0.35, -0.07, -370237, -368889, 102.54),
    ("12:50", 102.30, -0.30, -0.08, -369709, -369509, 102.48),
    ("12:55", 102.15, -0.30, -0.09, -371628, -370525, 102.42),
    ("13:00", 102.35,  0.10, -0.08, -370913, -370750, 102.40),
    ("13:05", 102.80,  0.50, -0.04, -370091, -370877, 102.46),
    ("13:10", 102.75,  0.15,  0.15, -369589, -369864, 102.52),
    ("13:15", 102.70, -0.10,  0.10, -369866, -369849, 102.58),
    ("13:20", 102.75, -0.05,  0.30, -369489, -369648, 102.63),
    ("13:25", 102.75, -0.05,  0.45, -368708, -369354, 102.68),
    ("13:30", 102.85,  0.05,  0.50, -367022, -368406, 102.73),

]

# ------------------------------------------------------------
# E003 - 2454.TW - 2026-08-07 - 5-minute evidence
# ------------------------------------------------------------

evidence_rows_E003 = [
    # time, close, MTM3, MTM10, OBV, OBV_MA3, BBI
    ("12:20", 3860, -15, -4.0, -2556, -2469, 3883.00),
    ("12:25", 3880,  -5, -4.0, -2470, -2498, 3881.44),
    ("12:30", 3875,   5, -6.0, -2501, -2509, 3880.58),
    ("12:35", 3885,  25, -5.5, -2448, -2473, 3882.05),
    ("12:40", 3865, -15, -7.5, -2488, -2479, 3879.16),
    ("12:45", 3860, -15, -8.5, -2526, -2487, 3876.44),
    ("12:50", 3850, -35, -11.0, -2596, -2537, 3870.57),
    ("12:55", 3840, -25, -11.0, -2779, -2634, 3865.19),
    ("13:00", 3875,  15, -8.0, -2692, -2689, 3865.43),
    ("13:05", 3900,  50, -1.5, -2591, -2687, 3871.99),
    ("13:10", 3895,  55,  5.5, -2677, -2653, 3879.04),
    ("13:15", 3885,  10,  7.0, -2727, -2665, 3881.49),
    ("13:20", 3900,   0,  6.5, -2576, -2660, 3885.11),
    ("13:25", 3895,   0,  4.0, -2942, -2748, 3886.52),
    ("13:30", 3900,  15,  7.0, -2521, -2680, 3888.91),
]
# ------------------------------------------------------------
# E004 - XAUUSD - 2026-08-07 - 5-minute evidence
# ------------------------------------------------------------

evidence_rows_E004 = [
    # time, close, MTM3, MTM10, OBV, OBV_MA3, BBI
    ("19:15", 4319.49,  2.76,  7.05, None, None, 4319.08),
    ("19:20", 4320.38, -3.32,  6.66, None, None, 4319.27),
    ("19:25", 4324.23, -0.97,  8.44, None, None, 4319.91),
    ("19:30", 4324.97,  5.48,  7.77, None, None, 4320.82),
    ("19:35", 4324.96,  4.58,  8.19, None, None, 4321.61),
    ("19:40", 4323.28, -0.95,  5.08, None, None, 4322.00),
    ("19:45", 4322.83, -2.14,  5.52, None, None, 4322.15),
    ("19:50", 4323.82, -1.14,  7.09, None, None, 4322.28),
    ("19:55", 4325.74,  2.46,  2.04, None, None, 4322.66),
    ("20:05", 4319.67,  None,  None, None, None, None),
    ("20:15", 4314.89,  None,  None, None, None, None),
    ("20:25", 4310.52,  None,  None, None, None, None),
    ("20:30", 4311.10, -3.79, -12.18, None, None, 4315.81),
    ("20:35", 4360.40, 46.81,  None, None, None, 4323.20),
    ("20:45", 4366.41, 55.31,  None, None, None, 4340.55),
]


# Select evidence rows for current research run
evidence_rows = evidence_rows_E004

columns = [
    "time",
    "close",
    "MTM3",
    "MTM10",
    "OBV",
    "OBV_MA3",
    "BBI",
]



# ============================================================
# Select evidence rows by episode
# ============================================================

if episode["episode_id"] == "E001":
    selected_rows = evidence_rows
elif episode["episode_id"] == "E002":
    selected_rows = evidence_rows_E002
elif episode["episode_id"] == "E003":
    selected_rows = evidence_rows_E003
elif episode["episode_id"] == "E004":
    selected_rows = evidence_rows_E004
else:
    raise ValueError(
        f"Unknown episode_id: {episode['episode_id']}"
    )


evidence = pd.DataFrame(selected_rows, columns=columns)

# ------------------------------------------------------------
# Mark each observation relative to the known turning zone.
# ------------------------------------------------------------

def classify_role(time_text):
    if time_text < episode["turning_zone_start"]:
        return "LEAD"
    elif time_text <= episode["turning_zone_end"]:
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

output_file = report_folder / f'episode_{episode["episode_id"]}_evidence.csv'

evidence.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig",
)



print()
print("=" * 72)
print(f'{episode["episode_id"]} - EPISODE EVIDENCE TABLE')
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
print(f'{episode["episode_id"]} - FIRST DESCRIPTIVE TIMING EVENTS')
print("=" * 72)


print(
    f'Turning zone      : {episode["turning_zone_start"]} -> '
    f'{episode["turning_zone_end"]}'
)







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





