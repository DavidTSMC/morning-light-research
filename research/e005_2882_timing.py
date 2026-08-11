"""
Morning Light / MLTTE
E005 — 2882 Timing Prototype

Architecture:
Signal -> Timing -> Amount

Purpose:
Determine WHEN a valid signal becomes actionable.

Principles:
- 新
- 速
- 實
- 簡
"""

TICKER = "2882.TW"

EPISODE = {
    "episode_id": "E005",
    "ticker": "2882.TW",
    "date": "2026-07-29",
    "timeframe": "5m",
    "turning_price": 92.5,
    "research_type": "intraday_bottom_reversal",
    "purpose": "Signal -> Timing -> Amount",
    "turning_time": "12:50",
    "turning_price_type": "intrabar_low",

}


# ------------------------------------------------------------
# E005 - 2882 - 5-minute evidence around the 92.5 turning zone
# Missing values are intentionally preserved as None.
# ------------------------------------------------------------

evidence_rows_5m = [
    # time, close, MTM3, OBV, OBV_MA3, BBI,
    # BIAS3, BIAS6, DI_PLUS, DI_MINUS, DIF, MACD

    ("12:30", 93.2, -0.20, -1516, -1449, 93.41,
     None, None, None, None, None, None),

    ("12:35", 93.3,  0.30, -1288, -1362, 93.43,
     None, None, None, None, None, None),

    ("12:50", 92.8, -0.50, -1901, -2109, 93.15,
     None, None, None, None, None, None),

    ("12:55", 93.4,  0.30, -1345, -1923, 93.18,
     None, None, None, None, None, None),

    ("13:00", 93.7,  1.00,  -892, -1379, 93.30,
     None, None, None, None, None, None),

    ("13:10", 93.8, None, None, None, None,
      0.21, 0.55, 13.84, 21.95, -0.25, -0.34),

    ("13:15", 94.2, None, None, None, None,
      0.46, 0.71, 20.08, 19.36, -0.17, -0.31),

    ("13:20", 94.0, None, None, None, None,
      0.00, 0.28, 18.76, 18.08, -0.11, -0.27),

    ("13:25", 93.7, None, None, None, None,
     -0.28, -0.09, 20.16, 15.83, -0.08, -0.23),

    ("13:30", 94.1, None, None, None, None,
      0.18, 0.27, 19.13, 15.02, -0.03, -0.19),
]

# ------------------------------------------------------------
# E005 v0.2 - Oscillator evidence
# Source: captured 2882 snapshots around the 92.5 turning episode.
# Do not interpolate missing timestamps.
# ------------------------------------------------------------

oscillator_rows_5m = [
    # time, close, WR5, WR10, J, PSY12, PSY24

    ("12:30", 93.2, -80.00, -87.18,  3.58, 25.00, 37.50),
    ("13:00", 93.7, -52.00, -70.73, 20.56, 33.33, 37.50),
    ("13:30", 94.1, -23.81, -60.98, 36.66, 33.33, 37.50),
]


def detect_oscillator_events(rows):
    events = []

    TIME = 0
    CLOSE = 1
    WR5 = 2
    WR10 = 3
    J = 4
    PSY12 = 5
    PSY24 = 6

    # WR5 recovery from oversold area
    for prev, curr in zip(rows, rows[1:]):
        if prev[WR5] <= -80 and curr[WR5] > -80:
            events.append(
                ("WR5_RECOVERY", curr[TIME], curr[CLOSE], "EARLY_RECOVERY")
            )
            break

    # WR5 above -50
    for r in rows:
        if r[WR5] > -50:
            events.append(
                ("WR5_ABOVE_-50", r[TIME], r[CLOSE], "MOMENTUM_RECOVERY")
            )
            break

    # J observed rising
    for prev, curr in zip(rows, rows[1:]):
        if curr[J] > prev[J]:
            events.append(
                ("J_RISING_OBSERVED", curr[TIME], curr[CLOSE], "EARLY_RECOVERY")
            )
            break

    # J above 20
    for r in rows:
        if r[J] > 20:
            events.append(
                ("J_ABOVE_20", r[TIME], r[CLOSE], "RECOVERY")
            )
            break

    # PSY12 rising
    for prev, curr in zip(rows, rows[1:]):
        if curr[PSY12] > prev[PSY12]:
            events.append(
                ("PSY12_RISING", curr[TIME], curr[CLOSE], "CONFIRM")
            )
            break

    events.sort(key=lambda x: x[1])
    return events

def build_unified_timeline(signal_events, oscillator_events, t0_str):
    unified = []

    for source, source_events in [
        ("SIGNAL", signal_events),
        ("OSC", oscillator_events),
    ]:
        for event, time, price, role in source_events:
            delta = minutes_from_t0(time, t0_str)

            unified.append(
                {
                    "time": time,
                    "delta": delta,
                    "event": event,
                    "price": price,
                    "role": role,
                    "source": source,
                }
            )

    unified.sort(
        key=lambda x: (
            x["delta"],
            x["time"],
            x["source"],
            x["event"],
        )
    )

    return unified


def main():
    print("Morning Light E005 – 2882 Timing")
    print("Signal -> Timing -> Amount")
    print()
    print("Episode loaded:")
    for key, value in EPISODE.items():
        print(f"{key:16}: {value}")

    print()
    print("5-minute evidence rows:")
    print(f"rows captured   : {len(evidence_rows_5m)}")

    print()
    print("time   close   MTM3   BIAS3   BIAS6   +DI     -DI")
    print("-" * 58)

    for row in evidence_rows_5m:
        (
            time,
            close,
            mtm3,
            obv,
            obv_ma3,
            bbi,
            bias3,
            bias6,
            di_plus,
            di_minus,
            dif,
            macd,
        ) = row

        print(
            f"{time:5}  "
            f"{close:5.1f}  "
            f"{str(mtm3):>5}  "
            f"{str(bias3):>6}  "
            f"{str(bias6):>6}  "
            f"{str(di_plus):>6}  "
            f"{str(di_minus):>6}"
        )

def detect_signal_events(rows):
    events = []




    # Column positions
    TIME = 0
    CLOSE = 1
    MTM3 = 2
    BIAS3 = 6
    BIAS6 = 7
    DI_PLUS = 8
    DI_MINUS = 9
    DIF = 10
    MACD = 11

    # --------------------------------------------------------
    # 1. MTM3 sequence
    # --------------------------------------------------------
    mtm_rows = [r for r in rows if r[MTM3] is not None]

    positive_crosses = []

    for prev, curr in zip(mtm_rows, mtm_rows[1:]):
        if prev[MTM3] <= 0 < curr[MTM3]:
            positive_crosses.append(curr)

    if positive_crosses:
        r = positive_crosses[0]
        events.append(
            ("MTM3_FIRST_CROSS", r[TIME], r[CLOSE], "LEAD")
        )

    if len(positive_crosses) >= 2:
        r = positive_crosses[1]
        events.append(
            ("MTM3_SECOND_LEG", r[TIME], r[CLOSE],
             "SECOND_LEG_CONFIRMATION")
        )

    # First negative MTM3 after first positive cross = retest
    if positive_crosses:
        first_cross_time = positive_crosses[0][TIME]
        after_first = False

        for r in mtm_rows:
            if r[TIME] == first_cross_time:
                after_first = True
                continue

            if after_first and r[MTM3] < 0:
                events.append(
                    ("MTM3_RETEST", r[TIME], r[CLOSE], "RETEST")
                )
                break

    # MTM3 expansion: strongest observed positive value
    positive_mtm = [r for r in mtm_rows if r[MTM3] > 0]

    if positive_mtm:
        r = max(positive_mtm, key=lambda x: x[MTM3])
        events.append(
            ("MTM3_EXPANSION", r[TIME], r[CLOSE], "MOMENTUM_CONFIRM")
        )

    # --------------------------------------------------------
    # 2. BIAS events
    # --------------------------------------------------------
    for r in rows:
        if r[BIAS3] is not None and r[BIAS3] > 0:
            events.append(
                ("BIAS3_POSITIVE", r[TIME], r[CLOSE], "BRIDGE")
            )
            break

    for r in rows:
        if (
            r[BIAS3] is not None
            and r[BIAS6] is not None
            and r[BIAS3] > 0
            and r[BIAS6] > 0
        ):
            events.append(
                ("BIAS3_6_POSITIVE", r[TIME], r[CLOSE], "CONFIRM")
            )
            break

    # --------------------------------------------------------
    # 3. DMI confirmation
    # --------------------------------------------------------
    for r in rows:
        if (
            r[DI_PLUS] is not None
            and r[DI_MINUS] is not None
            and r[DI_PLUS] > r[DI_MINUS]
        ):
            events.append(
                ("DMI_BULL_CROSS", r[TIME], r[CLOSE], "CONFIRM")
            )
            break

    # --------------------------------------------------------
    # 4. DIF-MACD relation
    #    Descriptive only — no trading interpretation yet.
    # --------------------------------------------------------
    for r in rows:
        if (
            r[DIF] is not None
            and r[MACD] is not None
            and r[DIF] > r[MACD]
        ):
            events.append(
                ("DIF_ABOVE_MACD", r[TIME], r[CLOSE], "CONFIRM")
            )
            break

        events.sort(key=lambda x: x[1])
        return events

def minutes_from_t0(time_str, t0_str):
    h, m = map(int, time_str.split(":"))
    t0_h, t0_m = map(int, t0_str.split(":"))

    minutes = h * 60 + m
    t0_minutes = t0_h * 60 + t0_m

    return minutes - t0_minutes
   

events = detect_signal_events(evidence_rows_5m)

print()
print("=" * 72)
print("E005 - SIGNAL SEQUENCE v0.1")
print("=" * 72)

for event, time, price, role in events:
    delta = minutes_from_t0(time, EPISODE["turning_time"])

    print(
        f"{time:5} | "
        f"T{delta:+3} min | "
        f"{event:22} | "
        f"price={price:5.1f} | "
        f"{role}"
    )

osc_events = detect_oscillator_events(oscillator_rows_5m)

print()
print("=" * 72)
print("E005 - OSCILLATOR SEQUENCE v0.2")
print("=" * 72)

for event, time, price, role in osc_events:
    delta = minutes_from_t0(time, EPISODE["turning_time"])

    print(
        f"{time:5} | "
        f"T{delta:+3} min | "
        f"{event:22} | "
        f"price={price:5.1f} | "
        f"{role}"
    )

unified = build_unified_timeline(
        events,
        osc_events,
        EPISODE["turning_time"],

)

   
print()
print("=" * 88)
print("E005 - UNIFIED TIMING TABLE v0.3")
print("=" * 88)

print(
        f"{'TIME':5} | {'T0':8} | {'EVENT':22} | "
        f"{'PRICE':7} | {'ROLE':24} | SOURCE"
    )
print("-" * 88)



for row in unified:
        print(
            f"{row['time']:5} | "
            f"T{row['delta']:+3} min | "
            f"{row['event']:22} | "
            f"{row['price']:7.1f} | "
            f"{row['role']:24} | "
            f"{row['source']}"
        )

# ------------------------------------------------------------
# E005 v0.4 - State Mapping
# Signal -> Timing -> Amount
# Descriptive prototype only.
# No position sizing yet.
# ------------------------------------------------------------

def map_state(role):
    if role in ("LEAD", "EARLY_RECOVERY"):
        return "WATCH"

    if role in ("RETEST", "SECOND_LEG_CONFIRMATION"):
        return "PROBE"

    if role in ("MOMENTUM_CONFIRM", "RECOVERY", "BRIDGE"):
        return "ADD"

    if role in ("CONFIRM", "MOMENTUM_RECOVERY"):
        return "CONFIRM"

    return "WATCH"

print()
print("=" * 104)
print("E005 - STATE MAPPING v0.4")
print("=" * 104)
print(
    f"{'TIME':5} | {'T0':8} | {'EVENT':22} | "
    f"{'ROLE':24} | {'STATE':8} | SOURCE"
)
print("-" * 104)

for row in unified:
    state = map_state(row["role"])

    print(
        f"{row['time']:5} | "
        f"T{row['delta']:+3} min | "
        f"{row['event']:22} | "
        f"{row['role']:24} | "
        f"{state:8} | "
        f"{row['source']}"
    )


def validate_states(rows):
    counts = {}

    for row in rows:
        state = map_state(row["role"])
        counts[state] = counts.get(state, 0) + 1

    print()
    print("=" * 72)
    print("E005 - STATE VALIDATION v0.5")
    print("=" * 72)

    for state in ("WATCH", "PROBE", "ADD", "CONFIRM"):
        print(f"{state:8} : {counts.get(state, 0)}")

    print("=" * 72)


def build_timing_ladder(rows):
    ladder = []

    stage_order = {
        "WATCH": 1,
        "PROBE": 2,
        "ADD": 3,
        "CONFIRM": 4,
    }

    for row in rows:
        state = map_state(row["role"])

        ladder.append({
            "time": row["time"],
            "delta": row["delta"],
            "event": row["event"],
            "role": row["role"],
            "state": state,
            "stage": stage_order[state],
            "source": row["source"],
        })

    ladder.sort(key=lambda x: (x["delta"], x["stage"]))

    return ladder


def timing_phase(delta):
    if delta < 0:
        return "LEAD"

    if 0 <= delta <= 5:
        return "TURN"

    if 5 < delta <= 10:
        return "RESONANCE"

    if 10 < delta <= 20:
        return "BRIDGE"

    return "CONFIRM"


if __name__ == "__main__":
    main()
    validate_states(unified)
    timing_ladder = build_timing_ladder(unified)

    print()
    print("E005 v0.6 - TIMING LADDER")
    print(f"ladder rows: {len(timing_ladder)}")   


    print()
    print("=" * 72)
    print("E005 v0.7 - TIMING PHASE TEST")
    print("=" * 72)

    for row in timing_ladder:
        phase = timing_phase(row["delta"])

        print(
            f"{row['time']:5} | "
            f"T{row['delta']:+3} min | "
            f"{phase:10} | "
            f"{row['event']:22} | "
            f"{row['state']:8}"
        )




print("-" * 96)
print(
    f"{'TIME':5} | {'T0':8} | {'STAGE':5} | "
    f"{'STATE':8} | {'EVENT':22} | {'ROLE':24} | SOURCE"
)
print("-" * 96)

for row in timing_ladder:
    print(
        f"{row['time']:5} | "
        f"T{row['delta']:+3} min | "
        f"{row['stage']:5} | "
        f"{row['state']:8} | "
        f"{row['event']:22} | "
        f"{row['role']:24} | "
        f"{row['source']}"
    )


# ============================================================
# E005 v0.8 — MORNING LIGHT STAGE MAPPING
# Research layer only — does not alter existing evidence
# ============================================================

STAGE_MAP = {
    "WATCH": "EARLY",
    "PROBE": "EARLY",
    "ADD": "CONFIRMING",
    "CONFIRM": "FULL_POWER",
}

print()
print("=" * 96)
print("E005 v0.8 - MORNING LIGHT STAGE MAPPING")
print("=" * 96)

for row in timing_ladder:
    ml_stage = STAGE_MAP.get(row["state"], "UNCLASSIFIED")

    print(
        f"{row['time']:5} | "
        f"T{row['delta']:+3} min | "
        f"{ml_stage:11} | "
        f"{row['event']:22} | "
        f"{row['role']:24}"
    )



# ============================================================
# E005 v0.9A — EVIDENCE FAMILY CLASSIFICATION
# Purpose:
#   Classify each timing event by evidence family.
#   Do NOT count correlated indicators as independent evidence.
# ============================================================

def evidence_family(event):
    event = str(event).upper()

    if "MTM" in event:
        return "MOMENTUM"

    if any(x in event for x in ["WR", "W/R", "J_", "PSY"]):
        return "OSCILLATOR"

    if "BIAS" in event:
        return "STRUCTURE"

    if any(x in event for x in ["DMI", "DI_OSC", "ADX"]):
        return "REGIME"

    if any(x in event for x in ["OBV", "VOLUME", "VOL_"]):
        return "CAPITAL"

    if any(x in event for x in ["MACD", "DIF", "D-M", "DM_"]):
        return "TREND_MOMENTUM"

    return "OTHER"


print()
print("=" * 108)
print("E005 v0.9A - EVIDENCE FAMILY CLASSIFICATION")
print("=" * 108)

seen_families = set()

for row in timing_ladder:
    family = evidence_family(row["event"])
    seen_families.add(family)

    print(
        f"{row['time']:5} | "
        f"T{row['delta']:+3} min | "
        f"{family:15} | "
        f"{row['event']:22} | "
        f"{row['role']}"
    )

print("-" * 108)
print("Independent evidence families observed:")
print(", ".join(sorted(seen_families)))
print(f"Family count = {len(seen_families)}")


# ============================================================
# E005 v0.9B — TRUE / FALSE REGIME CHECK
#
# Logic:
#   1 family       -> REVERSAL_CANDIDATE
#   2+ families    -> BUILDING_CONFIRMATION
#   REGIME joins an existing evidence chain
#                  -> REGIME_CONFIRMED
#
# Important:
#   REGIME alone does NOT confirm a true trend.
# ============================================================

print()
print("=" * 108)
print("E005 v0.9B - TRUE / FALSE REGIME CHECK")
print("=" * 108)

active_families = set()

for row in timing_ladder:
    family = evidence_family(row["event"])

    # Families accumulate in chronological order.
    if family != "OTHER":
        active_families.add(family)

    independent_count = len(active_families)

    if (
        "REGIME" in active_families
        and independent_count >= 3
    ):
        regime = "REGIME_CONFIRMED"

    elif independent_count >= 2:
        regime = "BUILDING_CONFIRMATION"

    elif independent_count == 1:
        regime = "REVERSAL_CANDIDATE"

    else:
        regime = "UNCLASSIFIED"

    print(
        f"{row['time']:5} | "
        f"T{row['delta']:+3} min | "
        f"{family:15} | "
        f"{independent_count}F | "
        f"{regime:22} | "
        f"{row['event']}"
    )
# ============================================================
# E005 v0.9C — CASCADE STATE PROTOTYPE
# Research evidence from the 2882 Daily bearish episode.
#
# IMPORTANT:
# PAUSE != REVERSAL
# INVALIDATED requires contrary evidence; not auto-triggered yet.
# ============================================================

bearish_cascade_evidence = [
    {
        "date": "2026-06-17",
        "state": "ATTEMPT",
        "families": ["OSCILLATOR", "STRUCTURE"],
        "evidence": "WR_J_BIAS3_EARLY_WEAKENING",
    },
    {
        "date": "2026-06-18",
        "state": "FORMING",
        "families": ["MOMENTUM", "STRUCTURE"],
        "evidence": "MTM3_AND_MULTI_BIAS_A_TURN",
    },
    {
        "date": "2026-06-22",
        "state": "PROPAGATING",
        "families": ["OSCILLATOR", "MOMENTUM", "STRUCTURE"],
        "evidence": "SECOND_TOP_FAILED_REEXPANSION",
    },
    {
        "date": "2026-06-24",
        "state": "PROPAGATING",
        "families": ["MOMENTUM", "STRUCTURE"],
        "evidence": "MTM3_BIAS3_BIAS5_BELOW_ZERO",
    },
    {
        "date": "2026-06-25",
        "state": "PAUSE",
        "families": ["OSCILLATOR", "MOMENTUM", "STRUCTURE"],
        "evidence": "SHORT_REBOUND_NOT_REVERSAL",
    },
    {
        "date": "2026-06-26",
        "state": "PROPAGATING",
        "families": ["TREND_MOMENTUM", "STRUCTURE"],
        "evidence": "D_M_AND_BIAS10_BELOW_ZERO",
    },
    {
        "date": "2026-06-30",
        "state": "REGIME_CONFIRMED",
        "families": ["REGIME"],
        "evidence": "DI_OSC_BELOW_ZERO",
    },
]

print()
print("=" * 112)
print("E005 v0.9C - BEARISH CASCADE STATE PROTOTYPE")
print("=" * 112)

for row in bearish_cascade_evidence:
    families = "+".join(row["families"])
    print(
        f"{row['date']} | "
        f"{row['state']:16} | "
        f"{families:38} | "
        f"{row['evidence']}"
    )

print("-" * 112)
print("RULE: PAUSE != REVERSAL")
print("RULE: CASCADE != RESONANCE")
print("RULE: INVALIDATION requires contrary evidence.")
print("RULE: Evidence propagates through time.")