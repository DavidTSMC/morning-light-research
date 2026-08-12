from pathlib import Path

BUDGETS = [0.25, 0.50, 1.00]
DISTANCES = [2.0, 3.0, 5.0]

print("=" * 72)
print("INDIVIDUAL RISK BUDGET v0.1 — POSITION SIZE GEOMETRY")
print("SCENARIO LENSES ONLY — NOT PRODUCTION PARAMETERS")
print("=" * 72)

print("\nA. RAW POSITION SIZE")
print("-" * 72)

for b in BUDGETS:
    for d in DISTANCES:
        size = b / d * 100
        print(
            f"Risk Budget={b:4.2f}% | "
            f"Risk Distance={d:3.1f}% | "
            f"Raw Position={size:6.2f}%"
        )

print("\nB. EQUAL AMOUNT != EQUAL RISK")
print("-" * 72)

for size in [10, 20, 30]:
    for d in DISTANCES:
        risk = size / 100 * d
        print(
            f"Position={size:2d}% | "
            f"Distance={d:3.1f}% | "
            f"Portfolio Risk={risk:4.2f}%"
        )

print("\n" + "=" * 72)
print("Risk Budget != Position Size")
print("Risk Distance != automatic stop-loss")
print("Raw Position != Final Deployment")
print("=" * 72)
