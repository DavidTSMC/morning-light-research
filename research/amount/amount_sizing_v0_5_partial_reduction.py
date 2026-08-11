import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import redirect_stdout

INFILE = Path("reports/amount/amount_sizing_v0_3R_events.csv")
OUTFILE = Path("reports/amount/amount_sizing_v0_5_partial_reduction.txt")

ev = pd.read_csv(INFILE)

THRESHOLDS = [-2, -3, -5]

STATES = [
    "INTACT",
    "EARLY_WARNING",
    "MOMENTUM_DETERIORATION",
    "DM_STATE_CHANGE",
]

# ============================================================
# POLICY DEFINITIONS
#
# All decisions occur at threshold-hit SAME-DAY CLOSE.
#
# EXIT:
#   0% exposure after hit.
#
# HALF:
#   reduce 50% at hit-close;
#   retain 50% exposure afterward.
#
# HOLD:
#   retain 100% exposure afterward.
#
# These are conceptual policy tests, not recommended allocations.
# ============================================================

def policy_returns(post_return):
    return {
        "EXIT_100": 0.0,
        "REDUCE_50": 0.5 * post_return,
        "HOLD_100": post_return,
    }


def report():

    print("=" * 120)
    print("AMOUNT SIZING v0.5 — PARTIAL REDUCTION POLICY TEST")
    print("SOURCE: FROZEN v0.3R EVENTS")
    print("ACTION POINT: THRESHOLD-HIT SAME-DAY CLOSE")
    print("POLICIES: EXIT 100% vs REDUCE 50% vs HOLD 100%")
    print("50% IS A NEUTRAL EXPERIMENT — NOT AN OPTIMIZED PARAMETER")
    print("=" * 120)

    # ========================================================
    # A. POLICY OUTCOME BY DISTANCE x STATE
    # ========================================================

    print()
    print("A. 5D POLICY OUTCOME BY DISTANCE × EVIDENCE STATE")
    print("=" * 120)

    for threshold in THRESHOLDS:

        print()
        print(f"THRESHOLD {threshold}%")
        print("-" * 85)

        for state in STATES:

            g = ev[
                (ev["Threshold"] == threshold)
                & (ev["State"] == state)
            ]

            if len(g) == 0:
                continue

            s = g["Post5D"].dropna()

            if len(s) == 0:
                continue

            print()
            print(f"{state} | N={len(s)}")

            for policy in [
                "EXIT_100",
                "REDUCE_50",
                "HOLD_100",
            ]:

                if policy == "EXIT_100":
                    p = pd.Series(
                        np.zeros(len(s)),
                        index=s.index
                    )

                elif policy == "REDUCE_50":
                    p = 0.5 * s

                else:
                    p = s

                print(
                    f"{policy:10} | "
                    f"mean={p.mean():6.2f}% | "
                    f"median={p.median():6.2f}% | "
                    f"negative={(p<0).mean()*100:5.1f}%"
                )

    # ========================================================
    # B. DETERIORATED STATES COLLAPSED
    # ========================================================

    print()
    print("B. DETERIORATED STATES — 5D POLICY COMPARISON")
    print("=" * 120)

    risky = [
        "MOMENTUM_DETERIORATION",
        "DM_STATE_CHANGE",
    ]

    for threshold in THRESHOLDS:

        g = ev[
            (ev["Threshold"] == threshold)
            & (ev["State"].isin(risky))
        ]

        s = g["Post5D"].dropna()

        if len(s) == 0:
            continue

        print()
        print(f"THRESHOLD {threshold}% | N={len(s)}")

        exit_ret = pd.Series(
            np.zeros(len(s)),
            index=s.index
        )
        half_ret = 0.5 * s
        hold_ret = s

        for label, p in [
            ("EXIT_100", exit_ret),
            ("REDUCE_50", half_ret),
            ("HOLD_100", hold_ret),
        ]:

            print(
                f"{label:10} | "
                f"mean={p.mean():6.2f}% | "
                f"median={p.median():6.2f}% | "
                f"negative={(p<0).mean()*100:5.1f}%"
            )

    # ========================================================
    # C. UPSIDE GIVEN UP vs DOWNSIDE AVOIDED
    #
    # For each event:
    # If Post5D > 0:
    #   reducing gives up half of that recovery.
    #
    # If Post5D < 0:
    #   reducing avoids half of that additional loss.
    # ========================================================

    print()
    print("C. WHAT DOES 50% REDUCTION BUY?")
    print("=" * 120)

    for threshold in THRESHOLDS:

        g = ev[
            (ev["Threshold"] == threshold)
            & (ev["State"].isin(risky))
        ].copy()

        s = g["Post5D"].dropna()

        if len(s) == 0:
            continue

        recovery = s[s > 0]
        continuation = s[s < 0]

        upside_given_up = (
            0.5 * recovery
        )

        downside_avoided = (
            -0.5 * continuation
        )

        print()
        print(f"THRESHOLD {threshold}% | N={len(s)}")

        print(
            f"Recovery cases     | N={len(recovery):3} | "
            f"mean recovery={recovery.mean():6.2f}%"
        )

        print(
            f"50% upside given up| "
            f"mean={upside_given_up.mean():6.2f}%"
            if len(upside_given_up)
            else
            "50% upside given up| N=0"
        )

        print(
            f"Loss-continuation  | N={len(continuation):3} | "
            f"mean continuation={continuation.mean():6.2f}%"
        )

        print(
            f"50% downside avoided | "
            f"mean={downside_avoided.mean():6.2f}%"
            if len(downside_avoided)
            else
            "50% downside avoided | N=0"
        )

    # ========================================================
    # D. FALSE-REDUCTION CONTROL
    # ========================================================

    print()
    print("D. FALSE-REDUCTION CONTROL — -2% + INTACT")
    print("=" * 120)

    g = ev[
        (ev["Threshold"] == -2)
        & (ev["State"] == "INTACT")
    ]

    s = g["Post5D"].dropna()

    print("N =", len(s))

    if len(s):

        print(
            f"HOLD_100   | mean={s.mean():6.2f}% | "
            f"median={s.median():6.2f}%"
        )

        print(
            f"REDUCE_50  | mean={(0.5*s).mean():6.2f}% | "
            f"median={(0.5*s).median():6.2f}%"
        )

        print(
            "Original T_action -> 10D | "
            f"mean={g['Final10D_from_Taction'].mean():6.2f}% | "
            f"winner={(g['Final10D_from_Taction']>0).mean()*100:5.1f}%"
        )

    # ========================================================
    # E. INTERPRETATION GUARDRAIL
    # ========================================================

    print()
    print("E. INTERPRETATION GUARDRAIL")
    print("=" * 120)

    print("REDUCE_50 cannot mathematically dominate both EXIT and HOLD")
    print("on raw mean return because it is exactly halfway between them.")
    print()
    print("Its research value is different:")
    print("- how much recovery participation is retained?")
    print("- how much continuation loss is avoided?")
    print("- does uncertainty justify reducing exposure rather than")
    print("  making an all-or-none decision?")

    print()
    print("=" * 120)
    print("AMOUNT SIZING v0.5 COMPLETE")
    print("PARTIAL REDUCTION IS A RISK-EXPOSURE POLICY,")
    print("NOT A MAGIC RETURN-OPTIMIZATION PARAMETER.")
    print("=" * 120)


OUTFILE.parent.mkdir(parents=True, exist_ok=True)

with OUTFILE.open("w", encoding="utf-8") as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUTFILE)
