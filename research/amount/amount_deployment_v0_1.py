# ============================================================
# MORNING LIGHT — AMOUNT DEPLOYMENT v0.1
# Offensive Capital Deployment State Machine
#
# PURPOSE
# Decide whether evidence PERMITS capital deployment to advance.
#
# IMPORTANT
# Permission to deploy != size permitted to deploy.
# Risk Budget determines the maximum permitted size separately.
# ============================================================

STATES = [
    "ZERO",
    "PROBE",
    "ADD",
    "HOLD",
]


def decide_deployment(
    current_state,
    technical_fresh_positive=False,
    new_independent_confirmation=False,
    thesis_intact=True,
    defensive_override=False,
):
    """
    v0.1 policy:

    ZERO -> PROBE
        requires a fresh positive Technical event.

    PROBE -> ADD
        requires a NEW independent confirmation.

    ADD -> HOLD
        when no new confirmation appears but thesis remains intact.

    HOLD -> HOLD
        while thesis remains intact and no new deployment event appears.

    Defensive deterioration does NOT decide reduction size here.
    It hands control to the defensive Amount / Risk modules.
    """

    if defensive_override or not thesis_intact:
        return "DEFENSIVE_OVERRIDE"

    if current_state == "ZERO":
        if technical_fresh_positive:
            return "PROBE"
        return "ZERO"

    if current_state == "PROBE":
        if new_independent_confirmation:
            return "ADD"
        return "PROBE"

    if current_state == "ADD":
        return "HOLD"

    if current_state == "HOLD":
        return "HOLD"

    raise ValueError(f"Unknown deployment state: {current_state}")


def run_blind_tests():
    cases = [
        ("ZERO",  False, False, True,  False, "ZERO"),
        ("ZERO",  True,  False, True,  False, "PROBE"),
        ("PROBE", False, False, True,  False, "PROBE"),
        ("PROBE", False, True,  True,  False, "ADD"),
        ("ADD",   False, False, True,  False, "HOLD"),
        ("HOLD",  False, False, True,  False, "HOLD"),
        ("PROBE", False, True,  False, False, "DEFENSIVE_OVERRIDE"),
        ("ADD",   False, False, True,  True,  "DEFENSIVE_OVERRIDE"),
    ]

    print("=" * 72)
    print("MORNING LIGHT — AMOUNT DEPLOYMENT v0.1")
    print("BLIND TEST — STATE TRANSITIONS ONLY")
    print("=" * 72)

    passed = 0

    for i, case in enumerate(cases, start=1):
        state, tech, confirm, intact, defensive, expected = case

        actual = decide_deployment(
            state,
            technical_fresh_positive=tech,
            new_independent_confirmation=confirm,
            thesis_intact=intact,
            defensive_override=defensive,
        )

        ok = actual == expected
        passed += int(ok)

        print(
            f"CASE {i}: {state:5} -> {actual:18} "
            f"| expected={expected:18} "
            f"| {'PASS' if ok else 'FAIL'}"
        )

    print("-" * 72)
    print(f"RESULT: {passed}/{len(cases)} PASS")


if __name__ == "__main__":
    run_blind_tests()