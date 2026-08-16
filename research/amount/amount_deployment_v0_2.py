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

# ============================================================
# EVIDENCE IDENTITY — v0.2
# ============================================================

VALID_SOURCES = {
    "TECHNICAL",
    "CROSS_MARKET",
    "CAPITAL",
}


def is_new_independent_confirmation(
    source,
    event_age,
    direction,
    already_used=False,
    origin_source=None,
):
    """
    A confirmation is eligible only when it is:

    1. From a recognized evidence source.
    2. Fresh: event_age == 0.
    3. Directionally positive.
    4. Not already consumed by an earlier deployment decision.
    5. Independent from the evidence source that triggered the
       current deployment step.
    """

    if source not in VALID_SOURCES:
        return False

    if event_age != 0:
        return False

    if direction != "UP":
        return False

    if already_used:
        return False

    if origin_source is not None and source == origin_source:
        return False

    return True


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

def run_evidence_identity_tests():
    cases = [
        # source, event_age, direction, used, origin, expected
        ("CROSS_MARKET", 0, "UP",   False, "TECHNICAL", True),
        ("CAPITAL",      0, "UP",   False, "TECHNICAL", True),

        # Not fresh
        ("CROSS_MARKET", 2, "UP",   False, "TECHNICAL", False),

        # Wrong direction
        ("CAPITAL",      0, "DOWN", False, "TECHNICAL", False),

        # Already consumed
        ("CROSS_MARKET", 0, "UP",   True,  "TECHNICAL", False),

        # Same family as origin
        ("TECHNICAL",    0, "UP",   False, "TECHNICAL", False),

        # Unknown source
        ("UNKNOWN",      0, "UP",   False, "TECHNICAL", False),

        # Fresh but neutral direction
        ("CAPITAL",      0, "FLAT", False, "TECHNICAL", False),
    ]

    print()
    print("=" * 72)
    print("EVIDENCE IDENTITY v0.2 — BLIND TEST")
    print("=" * 72)

    passed = 0

    for i, case in enumerate(cases, start=1):
        source, age, direction, used, origin, expected = case

        actual = is_new_independent_confirmation(
            source=source,
            event_age=age,
            direction=direction,
            already_used=used,
            origin_source=origin,
        )

        ok = actual == expected
        passed += int(ok)

        print(
            f"CASE {i}: {source:12} X{age} {direction:4} "
            f"used={str(used):5} origin={origin:10} "
            f"=> {actual} | expected={expected} "
            f"| {'PASS' if ok else 'FAIL'}"
        )

    print("-" * 72)
    print(f"EVIDENCE RESULT: {passed}/{len(cases)} PASS")



if __name__ == "__main__":
    run_blind_tests()
    run_evidence_identity_tests()





