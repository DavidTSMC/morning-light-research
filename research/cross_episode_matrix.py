"""
Morning Light Research
Cross-Episode Timing Matrix v0.1

Purpose:
Compare descriptive timing events across multiple episodes.

Evidence first.
No prediction.
No trading decision.
"""

import pandas as pd


print("=" * 72)
print("Morning Light Research")
print("Cross-Episode Timing Matrix v0.1")
print("Evidence First | Descriptive Comparison Only")
print("=" * 72)


from pathlib import Path

REPORTS_DIR = Path("reports")

episode_files = {
    "E001": REPORTS_DIR / "episode_E001_evidence.csv",
    "E002": REPORTS_DIR / "episode_E002_evidence.csv",
    "E003": REPORTS_DIR / "episode_E003_evidence.csv",

}

episodes = {}

for episode_id, file_path in episode_files.items():
    df = pd.read_csv(file_path)
    episodes[episode_id] = df

    print()
    print(f"{episode_id} loaded successfully")
    print(f"Rows      : {len(df)}")
    print(f"Ticker    : {df['ticker'].iloc[0]}")
    print(f"Start     : {df['time'].iloc[0]}")
    print(f"End       : {df['time'].iloc[-1]}")


def minutes_from_t0(event_time, t0):
    event = pd.to_datetime(event_time, format="%H:%M")
    reference = pd.to_datetime(t0, format="%H:%M")
    return int((event - reference).total_seconds() / 60)


print()
print("=" * 72)
print("DELTA-T NORMALIZATION TEST")
print("T0 = turning_zone_end")
print("=" * 72)

tests = [
    ("E001", "12:55", "13:00"),
    ("E001", "13:05", "13:00"),
    ("E002", "13:00", "13:00"),
    ("E002", "13:10", "13:00"),
]

for episode_id, event_time, t0 in tests:
    delta = minutes_from_t0(event_time, t0)
    print(f"{episode_id} | {event_time} vs T0 {t0} | Δt = {delta:+d} min")


# ============================================================
# AUTOMATIC EVENT DETECTION
# ============================================================

def first_positive_after_negative_or_zero_bridge(df, column):
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
    temp = df[["time", "OBV", "OBV_MA3"]].dropna().reset_index(drop=True)

    difference = temp["OBV"] - temp["OBV_MA3"]
    seen_below = False

    for i in range(len(temp)):
        if difference.iloc[i] < 0:
            seen_below = True

        elif difference.iloc[i] > 0 and seen_below:
            return temp.loc[i, "time"]

    return None


def first_bbi_upturn(df):
    temp = df[["time", "BBI"]].dropna().reset_index(drop=True)
    change = temp["BBI"].diff()

    for i in range(2, len(temp)):
        if change.iloc[i - 1] < 0 and change.iloc[i] > 0:
            return temp.loc[i, "time"]

    return None



# ============================================================
# BUILD CROSS-EPISODE TIMING MATRIX
# ============================================================

turning_zone_end = {
    "E001": "13:00",
    "E002": "13:00",
    "E003": "13:05",
}
matrix_rows = []

for episode_id, df in episodes.items():

    events = {
        "MTM3 zero-bridge":
            first_positive_after_negative_or_zero_bridge(df, "MTM3"),

        "OBV > OBV_MA3":
            first_obv_above_ma3_after_below(df),

        "BBI first upturn":
            first_bbi_upturn(df),

        "MTM10 first > 0":
            first_positive_after_negative_or_zero_bridge(df, "MTM10"),
    }

    for event_name, event_time in events.items():

        delta = None

        if event_time is not None:

            delta = minutes_from_t0(
                event_time,
                turning_zone_end[episode_id]
            )


        matrix_rows.append({
            "episode_id": episode_id,
            "ticker": df["ticker"].iloc[0],
            "event": event_name,
            "event_time": event_time,
            "delta_t_min": delta,
        })



matrix = pd.DataFrame(matrix_rows)

print()
print("=" * 72)
print("CROSS-EPISODE TIMING MATRIX v0.1")
print("T0 = turning_zone_end")
print("=" * 72)

print(matrix.to_string(index=False))


























