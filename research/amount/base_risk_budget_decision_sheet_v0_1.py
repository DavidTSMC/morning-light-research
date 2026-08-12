from pathlib import Path
from contextlib import redirect_stdout

OUT = Path(
    "reports/amount/base_risk_budget_decision_sheet_v0_1.txt"
)

BUDGETS = [0.25, 0.50, 1.00]
DISTANCES = [2.0, 3.0, 5.0]

# ============================================================
# IDENTITY-CLEAN EMPIRICAL STRESS
# From v0.5R2
# ============================================================

P95_FAILURE_STREAK = 4
MAX_FAILURE_STREAK = 5
MAX_SAME_DAY_FAILURES = 3
MAX_40D_FAILURES = 7

# ============================================================
# IMPORTANT
#
# Distance values below are GEOMETRY LENSES ONLY.
# They are NOT validated prospective stop/invalidation levels.
#
# Risk Budget values are SCENARIO LENSES ONLY.
# No production budget is assigned in v0.1.
# ============================================================


def raw_position(budget, distance):
    return budget / distance * 100


def report():

    print("=" * 122)
    print("BASE RISK BUDGET DECISION SHEET v0.1")
    print("MORNING LIGHT AMOUNT TRIPOD")
    print("ENOUGH TO MATTER | SMALL ENOUGH TO SURVIVE | FLEXIBLE ENOUGH TO RESPOND")
    print("=" * 122)

    # ========================================================
    # A. PARTICIPATION LEG
    # ========================================================

    print()
    print("A. PARTICIPATION — ENOUGH TO MATTER")
    print("=" * 122)

    for b in BUDGETS:

        print()
        print(f"BASE RISK BUDGET LENS = {b:.2f}%")

        for d in DISTANCES:

            p = raw_position(b, d)

            print(
                f"Geometry distance={d:3.1f}% | "
                f"Raw position={p:6.2f}%"
            )

    print()
    print(
        "NOTE: This section measures deployment geometry only."
    )

    print(
        "It does NOT claim that 2%, 3%, or 5% is the correct "
        "prospective invalidation distance."
    )

    # ========================================================
    # B. SURVIVAL LEG
    # ========================================================

    print()
    print("B. SURVIVAL — SMALL ENOUGH TO SURVIVE")
    print("=" * 122)

    for b in BUDGETS:

        p95 = b * P95_FAILURE_STREAK
        histmax = b * MAX_FAILURE_STREAK
        same_day = b * MAX_SAME_DAY_FAILURES
        cluster40 = b * MAX_40D_FAILURES

        print()
        print(f"BASE RISK BUDGET LENS = {b:.2f}%")

        print(
            f"P95 failure streak ({P95_FAILURE_STREAK}) "
            f"-> {p95:5.2f}% risk capacity"
        )

        print(
            f"Historical max streak ({MAX_FAILURE_STREAK}) "
            f"-> {histmax:5.2f}%"
        )

        print(
            f"Historical same-day max ({MAX_SAME_DAY_FAILURES}) "
            f"-> {same_day:5.2f}%"
        )

        print(
            f"40D max failure count ({MAX_40D_FAILURES}) "
            f"-> {cluster40:5.2f}%"
        )

    print()
    print(
        "NOTE: These are full-risk-consumption stress translations."
    )

    print(
        "They are NOT realized portfolio drawdowns."
    )

    # ========================================================
    # C. ADAPTATION LEG
    # ========================================================

    print()
    print("C. ADAPTATION — FLEXIBLE ENOUGH TO RESPOND")
    print("=" * 122)

    print(
        "Initial Base Risk Budget is NOT a promise to maintain "
        "the original Amount."
    )

    print()
    print("Dynamic evidence already under study:")
    print("- Bias3 deterioration / zero-line state change")
    print("- MTM3 deterioration / zero-line state change")
    print("- D-M state change")
    print("- Partial reduction")
    print("- Same-day vs delayed action timing")

    print()
    print(
        "Adaptation has DOWNWARD authority when evidence weakens."
    )

    print(
        "Adaptation does NOT automatically earn an initial "
        "Risk Budget uplift."
    )

    # ========================================================
    # D. TRIPOD REVIEW
    # ========================================================

    print()
    print("D. TRIPOD REVIEW")
    print("=" * 122)

    for b in BUDGETS:

        p3 = raw_position(b, 3.0)
        p5 = raw_position(b, 5.0)

        p95 = b * P95_FAILURE_STREAK
        max5 = b * MAX_FAILURE_STREAK
        same3 = b * MAX_SAME_DAY_FAILURES
        max40 = b * MAX_40D_FAILURES

        print()
        print(f"RISK BUDGET LENS = {b:.2f}%")

        print(
            f"Participation geometry: "
            f"3% lens -> {p3:5.1f}% position | "
            f"5% lens -> {p5:5.1f}% position"
        )

        print(
            f"Survival stress: "
            f"P95 streak -> {p95:4.2f}% | "
            f"max streak -> {max5:4.2f}% | "
            f"same-day max -> {same3:4.2f}% | "
            f"40D max -> {max40:4.2f}%"
        )

        print(
            "Adaptation: dynamic downward authority retained"
        )

    # ========================================================
    # E. WHAT IS PROVEN / NOT PROVEN
    # ========================================================

    print()
    print("E. EVIDENCE BOUNDARY")
    print("=" * 122)

    print("PROVEN / SUPPORTED:")
    print("- A2 earns a common Base Risk Permission.")
    print("- Amount scales edge; Amount does not create edge.")
    print("- Duplicate detections do not create extra capital permission.")
    print("- Historical failure streaks and joint failures exist.")
    print("- Cluster risk deserves ceiling authority.")
    print("- Dynamic deterioration can justify action review/reduction.")

    print()
    print("NOT YET PROVEN:")
    print("- The production Base Risk Budget percentage.")
    print("- A universal prospective Risk Distance.")
    print("- 0.50% as the final default.")
    print("- Any automatic Risk Budget uplift.")
    print("- Any fixed Cluster haircut percentage.")

    # ========================================================
    # F. BOARD DECISION
    # ========================================================

    print()
    print("F. BOARD DECISION — v0.1")
    print("=" * 122)

    print(
        "0.25%, 0.50%, and 1.00% remain scenario lenses."
    )

    print(
        "0.50% may remain a MIDDLE OPERATING LENS, "
        "but is NOT promoted to production."
    )

    print()
    print(
        "Next missing evidence:"
    )

    print(
        "Define and validate a PROSPECTIVE, T_action-known "
        "Risk Distance before converting Base Risk Budget "
        "into live position size."
    )

    print()
    print("=" * 122)
    print("三足鼎立，缺一不穩；三足制衡，方能載重。")
    print("=" * 122)


OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUT.open(
    "w",
    encoding="utf-8"
) as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT)
