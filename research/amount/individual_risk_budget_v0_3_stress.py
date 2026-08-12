from pathlib import Path
from contextlib import redirect_stdout

OUT = Path(
    "reports/amount/individual_risk_budget_v0_3_stress.txt"
)

BUDGETS = [
    0.25,
    0.50,
    1.00,
]

LOSS_COUNTS = [
    1, 2, 3, 4, 5,
]

START_CAPITAL = 100.0


def sequential_equity(
    start,
    risk_pct,
    n_losses
):
    """
    Each new thesis risks risk_pct of CURRENT equity.
    Therefore losses compound geometrically.
    """

    equity = start

    for _ in range(n_losses):
        equity *= (
            1 - risk_pct / 100
        )

    return equity


def report():

    print("=" * 116)
    print("INDIVIDUAL RISK BUDGET v0.3 — PORTFOLIO DAMAGE STRESS TEST")
    print("COMMON BASE RISK BUDGET — SURVIVAL GEOMETRY")
    print("NO RETURN OPTIMIZATION | NO PRODUCTION PARAMETER ASSIGNED")
    print("=" * 116)

    # ========================================================
    # A. SEQUENTIAL LOSS STRESS
    # ========================================================

    print()
    print("A. SEQUENTIAL THESIS FAILURES")
    print("=" * 116)

    for b in BUDGETS:

        print()
        print(f"BASE RISK BUDGET = {b:.2f}%")

        for n in LOSS_COUNTS:

            equity = sequential_equity(
                START_CAPITAL,
                b,
                n
            )

            drawdown = (
                equity / START_CAPITAL - 1
            ) * 100

            print(
                f"{n} consecutive failures | "
                f"equity={equity:7.3f} | "
                f"portfolio damage={drawdown:7.3f}%"
            )

    # ========================================================
    # B. CONCURRENT FAILURE STRESS
    #
    # Approximation:
    # multiple independent thesis budgets are simultaneously
    # fully consumed before resizing can occur.
    # ========================================================

    print()
    print("B. CONCURRENT OPEN-RISK FAILURE")
    print("=" * 116)

    for b in BUDGETS:

        print()
        print(f"BASE RISK BUDGET = {b:.2f}%")

        for n in LOSS_COUNTS:

            damage = b * n

            remaining = (
                100 - damage
            )

            print(
                f"{n} simultaneous failures | "
                f"open risk={damage:5.2f}% | "
                f"capital remaining={remaining:6.2f}%"
            )

    # ========================================================
    # C. RECOVERY BURDEN
    #
    # After a drawdown D, required gain to recover:
    #
    # recovery = 100/(100-D) - 1
    # ========================================================

    print()
    print("C. RECOVERY BURDEN AFTER CONCURRENT DAMAGE")
    print("=" * 116)

    for b in BUDGETS:

        print()
        print(f"BASE RISK BUDGET = {b:.2f}%")

        for n in [2,3,4,5]:

            damage = b * n
            remaining = 100 - damage

            recovery = (
                100 / remaining - 1
            ) * 100

            print(
                f"{n} failures | "
                f"damage={damage:5.2f}% | "
                f"gain needed to recover={recovery:5.2f}%"
            )

    # ========================================================
    # D. CLUSTER STRESS BRIDGE
    #
    # We already observed that multiple A2 positions can
    # experience joint downside.
    #
    # This section does NOT estimate cluster probabilities.
    # It only translates N jointly-consumed risk budgets
    # into portfolio damage.
    # ========================================================

    print()
    print("D. CLUSTER / JOINT-DAMAGE GEOMETRY")
    print("=" * 116)

    for b in BUDGETS:

        two = 2 * b
        three = 3 * b
        four = 4 * b

        print(
            f"Budget={b:4.2f}% | "
            f"2 joint={two:4.2f}% | "
            f"3 joint={three:4.2f}% | "
            f"4 joint={four:4.2f}%"
        )

    # ========================================================
    # E. SURVIVAL VS PARTICIPATION
    # ========================================================

    print()
    print("E. INTERPRETATION")
    print("=" * 116)

    print(
        "Smaller Base Risk Budget improves survival "
        "but may reduce market participation."
    )

    print(
        "Larger Base Risk Budget improves deployment "
        "but consumes portfolio damage capacity faster."
    )

    print()
    print(
        "This test does NOT determine the optimal budget."
    )

    print(
        "It defines the damage geometry that any future "
        "budget decision must respect."
    )

    print()
    print(
        "Cluster and Aggregate Portfolio ceilings remain "
        "necessary because multiple A2 theses can fail together."
    )

    print()
    print(
        "Macro stress may later reduce permission, "
        "but is deliberately excluded from this test."
    )

    # ========================================================
    # F. GUARDRAILS
    # ========================================================

    print()
    print("F. GUARDRAILS")
    print("=" * 116)

    print("1. Common Base Risk Budget != Final Position Size.")
    print("2. Risk Budget != fixed stop-loss.")
    print("3. Stress lenses are not production recommendations.")
    print("4. No scenario is selected because it produces better returns.")
    print("5. Survival capacity precedes return optimization.")

    print()
    print("=" * 116)
    print("INDIVIDUAL RISK BUDGET v0.3 COMPLETE")
    print("QUESTION: HOW MUCH DAMAGE CAN REPEATED A2 FAILURE CAUSE?")
    print("=" * 116)


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
