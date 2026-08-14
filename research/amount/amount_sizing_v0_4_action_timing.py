import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

INFILE = Path("reports/amount/amount_sizing_v0_3R_events.csv")
OUTFILE = Path("reports/amount/amount_sizing_v0_4_action_timing.txt")

ev = pd.read_csv(INFILE)

STATES = [
    "INTACT",
    "EARLY_WARNING",
    "MOMENTUM_DETERIORATION",
    "DM_STATE_CHANGE",
]

THRESHOLDS = [-2, -3, -5]

# ============================================================
# IMPORTANT:
# v0.4 does NOT reconstruct indicators.
# It uses the frozen v0.3R event-level output only.
#
# Post1D/Post3D/Post5D:
# return from threshold-hit CLOSE to future close.
#
# Final10D_from_Taction:
# original outcome from A2 T_action to Day 10.
# ============================================================

def stats(s):
    s = s.dropna()
    if len(s) == 0:
        return None
    return {
        "N": len(s),
        "mean": s.mean(),
        "median": s.median(),
        "positive": (s > 0).mean() * 100,
        "negative": (s < 0).mean() * 100,
    }

def report():

    print("=" * 118)
    print("AMOUNT SIZING v0.4 — INVALIDATION -> ACTION TIMING")
    print("SOURCE: FROZEN v0.3R EVENT CSV")
    print("NO INDICATORS OR DISTANCE THRESHOLDS RECOMPUTED")
    print("=" * 118)

    # ========================================================
    # A. EVENT COUNTS
    # ========================================================

    print()
    print("A. LOCKED EVENT COUNTS")
    print("=" * 118)

    print(
        pd.crosstab(
            ev["Threshold"],
            ev["State"]
        ).to_string()
    )

    # ========================================================
    # B. POST-HIT PATH
    # ========================================================

    print()
    print("B. POST-HIT PATH — WHAT HAPPENS IF WE WAIT?")
    print("=" * 118)

    for threshold in THRESHOLDS:

        print()
        print(f"THRESHOLD {threshold}%")
        print("-" * 80)

        for state in STATES:

            g = ev[
                (ev["Threshold"] == threshold)
                & (ev["State"] == state)
            ]

            if len(g) == 0:
                continue

            print()
            print(f"{state} | N={len(g)}")

            for day in [1,3,5]:

                z = stats(g[f"Post{day}D"])

                if z is None:
                    continue

                print(
                    f"WAIT {day}D | "
                    f"mean={z['mean']:6.2f}% | "
                    f"median={z['median']:6.2f}% | "
                    f"up={z['positive']:5.1f}% | "
                    f"down={z['negative']:5.1f}%"
                )

    # ========================================================
    # C. RECOVERY TEST
    #
    # Recovery here means price is above threshold-hit close
    # after the stated waiting period.
    # ========================================================

    print()
    print("C. RECOVERY RATE AFTER HIT")
    print("=" * 118)

    for threshold in THRESHOLDS:

        print()
        print(f"THRESHOLD {threshold}%")

        for state in STATES:

            g = ev[
                (ev["Threshold"] == threshold)
                & (ev["State"] == state)
            ]

            if len(g) == 0:
                continue

            vals = []

            for day in [1,3,5]:
                s = g[f"Post{day}D"].dropna()
                recovery = (s > 0).mean() * 100 if len(s) else np.nan
                vals.append(f"{day}D={recovery:5.1f}%")

            print(
                f"{state:24} | "
                f"N={len(g):3} | "
                + " | ".join(vals)
            )

    # ========================================================
    # D. DELAY VALUE RELATIVE TO IMMEDIATE EXIT
    #
    # Immediate exit at hit-close = 0% future change.
    # Positive PostXD => waiting X days beat immediate exit.
    # Negative PostXD => immediate exit preserved more capital.
    # ========================================================

    print()
    print("D. DOES WAITING BEAT IMMEDIATE EXIT?")
    print("=" * 118)

    for threshold in THRESHOLDS:

        print()
        print(f"THRESHOLD {threshold}%")

        for state in STATES:

            g = ev[
                (ev["Threshold"] == threshold)
                & (ev["State"] == state)
            ]

            if len(g) == 0:
                continue

            pieces = []

            for day in [1,3,5]:

                s = g[f"Post{day}D"].dropna()

                if len(s) == 0:
                    continue

                beat_exit = (s > 0).mean() * 100

                pieces.append(
                    f"{day}D wait-beats-exit={beat_exit:5.1f}%"
                )

            print(
                f"{state:24} | "
                f"N={len(g):3} | "
                + " | ".join(pieces)
            )

    # ========================================================
    # E. FALSE-EXIT CONTROL
    #
    # Especially important:
    # -2% + INTACT
    # If this group frequently recovers, fixed price stops
    # destroy healthy trades.
    # ========================================================

    print()
    print("E. FALSE-EXIT CONTROL — -2% + INTACT")
    print("=" * 118)

    control = ev[
        (ev["Threshold"] == -2)
        & (ev["State"] == "INTACT")
    ]

    print("N =", len(control))

    if len(control):

        print(
            "Original 10D from T_action | "
            f"mean={control['Final10D_from_Taction'].mean():6.2f}% | "
            f"median={control['Final10D_from_Taction'].median():6.2f}% | "
            f"winner={(control['Final10D_from_Taction']>0).mean()*100:5.1f}%"
        )

        for day in [1,3,5]:

            s = control[f"Post{day}D"].dropna()

            print(
                f"After hit WAIT {day}D | "
                f"mean={s.mean():6.2f}% | "
                f"median={s.median():6.2f}% | "
                f"recovery={(s>0).mean()*100:5.1f}%"
            )

    # ========================================================
    # F. HIGH-RISK COLLAPSED VIEW
    #
    # Do not invent a new state.
    # Merely summarize the two already-defined deterioration
    # states for descriptive action timing.
    # ========================================================

    print()
    print("F. DETERIORATED STATES — ACTION TIMING SUMMARY")
    print("=" * 118)

    risky_states = [
        "MOMENTUM_DETERIORATION",
        "DM_STATE_CHANGE",
    ]

    for threshold in THRESHOLDS:

        g = ev[
            (ev["Threshold"] == threshold)
            & (ev["State"].isin(risky_states))
        ]

        if len(g) == 0:
            continue

        print()
        print(f"THRESHOLD {threshold}% | N={len(g)}")

        for day in [1,3,5]:

            s = g[f"Post{day}D"].dropna()

            print(
                f"WAIT {day}D | "
                f"mean={s.mean():6.2f}% | "
                f"median={s.median():6.2f}% | "
                f"wait-beats-exit={(s>0).mean()*100:5.1f}%"
            )

    print()
    print("=" * 118)
    print("AMOUNT SIZING v0.4 COMPLETE")
    print("DIAGNOSIS DOES NOT AUTOMATICALLY DETERMINE EXECUTION TIMING.")
    print("A WARNING EARNS AN ACTION TEST; IT DOES NOT AUTOMATICALLY EARN AN EXIT.")
    print("=" * 118)


OUTFILE.parent.mkdir(parents=True, exist_ok=True)

with OUTFILE.open("w", encoding="utf-8") as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUTFILE)
