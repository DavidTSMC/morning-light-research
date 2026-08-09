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

if __name__ == "__main__":
    main()


