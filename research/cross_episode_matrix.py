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
from pathlib import Path
import matplotlib.pyplot as plt



print("=" * 72)
print("Morning Light Research")
print("Cross-Episode Timing Matrix v0.1")
print("Evidence First | Descriptive Comparison Only")
print("=" * 72)




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


# ============================================================
# CROSS-EPISODE STATISTICAL SUMMARY v0.2
# Evidence First | Descriptive Statistics Only
# ============================================================

summary = (
    matrix
    .dropna(subset=["delta_t_min"])
    .groupby("event")["delta_t_min"]
    .agg(
        n="count",
        mean_delta="mean",
        median_delta="median",
        min_delta="min",
        max_delta="max",
    )
    .reset_index()
)

summary["spread"] = summary["max_delta"] - summary["min_delta"]

print()
print("=" * 72)
print("CROSS-EPISODE STATISTICAL SUMMARY v0.2")
print("T0 = turning_zone_end")
print("Negative = before T0 | Positive = after T0")
print("=" * 72)

print(summary.to_string(index=False))

# ============================================================
# PLOT v0.21 - Overlap Expanded + Episode Labels
# ============================================================

plot_df = matrix.dropna(subset=["delta_t_min"]).copy()

# Event display order (bottom -> top)
event_order = [
    "OBV > OBV_MA3",
    "MTM3 zero-bridge",
    "BBI first upturn",
    "MTM10 first > 0",
]

event_to_y = {event: i for i, event in enumerate(event_order)}
plot_df["y"] = plot_df["event"].map(event_to_y)

# ------------------------------------------------------------
# Expand overlapping points
# If same event + same delta_t_min has multiple episodes,
# spread them slightly on x-axis so they can be seen separately.
# ------------------------------------------------------------
def symmetric_offsets(n, step=0.35):
    if n == 1:
        return [0.0]
    if n == 2:
        return [-step, step]
    if n == 3:
        return [-step, 0.0, step]

    center = (n - 1) / 2
    return [(i - center) * step for i in range(n)]

plot_df["plot_x"] = plot_df["delta_t_min"].astype(float)

for (event, delta), group in plot_df.groupby(["event", "delta_t_min"]):
    idxs = group.sort_values("episode_id").index.tolist()
    offsets = symmetric_offsets(len(idxs), step=0.35)
    for idx, off in zip(idxs, offsets):
        plot_df.loc[idx, "plot_x"] = plot_df.loc[idx, "delta_t_min"] + off

# ------------------------------------------------------------
# Plot
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.5))

episode_ids = sorted(plot_df["episode_id"].unique())

for episode_id in episode_ids:
    sub = plot_df[plot_df["episode_id"] == episode_id]

    ax.scatter(
        sub["plot_x"],
        sub["y"],
        s=110,
        label=episode_id,
        alpha=0.95,
    )

   # Episode label next to each point
# Labels on overlap-expanded points are placed outward
# so that they do not collide with each other.
for _, row in sub.iterrows():

    if row["plot_x"] < row["delta_t_min"]:
        # Point was shifted left: place label above-left
        label_offset = (-7, 8)
        horizontal_alignment = "right"

    elif row["plot_x"] > row["delta_t_min"]:
        # Point was shifted right: place label below-right
        label_offset = (7, -9)
        horizontal_alignment = "left"

    else:
        # Non-overlapping point: place label above-right
        label_offset = (7, 8)
        horizontal_alignment = "left"

    ax.annotate(
        row["episode_id"],
        xy=(row["plot_x"], row["y"]),
        xytext=label_offset,
        textcoords="offset points",
        fontsize=9,
        ha=horizontal_alignment,
        va="center",
    )



# T0 vertical line
ax.axvline(0, linestyle="--", linewidth=2)

# Axes / labels
ax.set_yticks(range(len(event_order)))
ax.set_yticklabels(event_order)
ax.set_xlabel("Delta Time from T0 (minutes)    <-- Earlier | Later -->")
ax.set_ylabel("Observed Event")
ax.set_title(
    "Morning Light Cross-Episode Timing Map v0.21\n"
    "Overlap Expanded + Episode Labels\n"
    "T0 = Turning Zone End"
)

ax.grid(True, linestyle=":", alpha=0.5)
ax.legend(title="Episode")

# ------------------------------------------------------------
# Save PNG
# ------------------------------------------------------------
output_png = REPORTS_DIR / "cross_episode_timing_map_v021.png"
plt.tight_layout()
plt.savefig(output_png, dpi=150, bbox_inches="tight")

print()
print("=" * 72)
print("PNG exported successfully")
print(f"Saved to : {output_png}")
print("=" * 72)

plt.show()
























































# ============================================================
# CROSS-EPISODE TIMING MAP v0.2
# Evidence First | Raw Timing Visualization
# ============================================================

import matplotlib.pyplot as plt

plot_data = matrix.dropna(subset=["delta_t_min"]).copy()

event_order = [
    "OBV > OBV_MA3",
    "MTM3 zero-bridge",
    "BBI first upturn",
    "MTM10 first > 0",
]

episode_ids = plot_data["episode_id"].unique()

fig, ax = plt.subplots(figsize=(11, 6))

for episode_id in episode_ids:
    subset = plot_data[plot_data["episode_id"] == episode_id]

    x_values = []
    y_values = []

    for event in event_order:
        row = subset[subset["event"] == event]

        if not row.empty:
            x_values.append(row["delta_t_min"].iloc[0])
            y_values.append(event)

    ax.scatter(
        x_values,
        y_values,
        s=90,
        label=episode_id,
    )

# T0 reference line
ax.axvline(
    x=0,
    linewidth=2,
    linestyle="--",
)

ax.set_title(
    "Morning Light Cross-Episode Timing Map v0.2\n"
    "T0 = Turning Zone End"
)

ax.set_xlabel(
    "Delta Time from T0 (minutes)   "
    "<-- Earlier | Later -->"
)

ax.set_ylabel("Observed Event")

ax.grid(
    True,
    axis="x",
    linestyle=":",
    alpha=0.5,
)

ax.legend(title="Episode")

plt.tight_layout()

plot_file = REPORTS_DIR / "cross_episode_timing_map_v0_2.png"

plt.savefig(
    plot_file,
    dpi=180,
    bbox_inches="tight",
)

plt.close()

print()
print(f"Timing map saved to: {plot_file}")













