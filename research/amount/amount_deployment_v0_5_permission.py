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


# ============================================================
# READINESS LAYER — v0.4
#
# Constitution:
# A valid Lead Event earns ARMED, not PROBE.
# Time does not earn permission. Evidence does.
#
# ARMED = Get Ready, not Get In.
# ============================================================

# ============================================================
# PROBE PERMISSION LAYER — v0.5
#
# Constitution:
# Lead Event earns ARMED.
# New qualified confirmation may earn PROBE permission.
#
# Permission != position size.
# Price movement alone is not evidence.
# ============================================================

def probe_permission(
    readiness,
    lead_invalidated=False,
    confirmation_fresh=False,
    confirmation_direction="FLAT",
    confirmation_unused=True,
    independence_level=0,
):
    """
    Independence hierarchy:

    L0 = same event / continuation
    L1 = same technical subgroup
    L2 = cross-subgroup confirmation
    L3 = cross-module confirmation

    v0.5 provisional rule:
    L0/L1 cannot earn PROBE.
    L2/L3 may earn PROBE permission.

    This threshold is a Constitution test candidate,
    not yet a historically validated production rule.
    """

    if readiness != "ARMED":
        return False

    if lead_invalidated:
        return False

    if not confirmation_fresh:
        return False

    if confirmation_direction != "UP":
        return False

    if not confirmation_unused:
        return False

    if independence_level < 2:
        return False

    return True


READINESS_STATES = [
    "QUIET",
    "ARMED",
]


def decide_readiness(
    current_readiness,
    valid_fresh_lead=False,
    lead_invalidated=False,
):
    """
    QUIET -> ARMED
        requires a valid fresh Lead Event.

    ARMED -> QUIET
        when the Lead Event is invalidated.

    ARMED -> ARMED
        while waiting for independent confirmation.

    Elapsed time alone never upgrades readiness or deployment.
    """

    if current_readiness not in READINESS_STATES:
        raise ValueError(
            f"Unknown readiness state: {current_readiness}"
        )

    if lead_invalidated:
        return "QUIET"

    if current_readiness == "QUIET":
        if valid_fresh_lead:
            return "ARMED"
        return "QUIET"

    return "ARMED"


# ============================================================
# EVIDENCE CONSUMPTION LEDGER — v0.3
#
# Constitution:
# One event, one deployment vote.
#
# An event may remain valid after consumption,
# but it cannot trigger another deployment upgrade.
# ============================================================

def make_event(
    event_id,
    source,
    event_type,
    event_date,
    event_age,
    direction,
):
    return {
        "event_id": event_id,
        "source": source,
        "event_type": event_type,
        "event_date": event_date,
        "event_age": event_age,
        "direction": direction,
        "consumed_by": None,
        "consumed_date": None,
    }

def consume_event(event, consumed_by, consumed_date):
    """
    Consume one evidence event for one deployment decision.

    Constitution:
    One event, one deployment vote.
    """

    if event["consumed_by"] is not None:
        return False

    event["consumed_by"] = consumed_by
    event["consumed_date"] = consumed_date

    return True


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


def run_consumption_ledger_tests():
    print()
    print("=" * 72)
    print("EVIDENCE CONSUMPTION LEDGER v0.3 — BLIND TEST")
    print("=" * 72)

    event = make_event(
        event_id="TECHNICAL:BIAS3:UP_CROSS:2026-06-09",
        source="TECHNICAL",
        event_type="BIAS3_UP_CROSS",
        event_date="2026-06-09",
        event_age=0,
        direction="UP",
    )

    results = []

    # CASE 1 — new event starts unused
    results.append((
        "New event is unused",
        event["consumed_by"] is None
        and event["consumed_date"] is None,
    ))

    # CASE 2 — first consumption is accepted
    first = consume_event(
        event,
        consumed_by="PROBE",
        consumed_date="2026-06-09",
    )
    results.append(("First consumption accepted", first is True))

    # CASE 3 — deployment decision is remembered
    results.append((
        "consumed_by remembered",
        event["consumed_by"] == "PROBE",
    ))

    # CASE 4 — consumption date is remembered
    results.append((
        "consumed_date remembered",
        event["consumed_date"] == "2026-06-09",
    ))

    # CASE 5 — same event cannot vote twice
    second = consume_event(
        event,
        consumed_by="ADD_1",
        consumed_date="2026-06-10",
    )
    results.append(("Second consumption rejected", second is False))

    # CASE 6 — rejected second vote cannot overwrite history
    results.append((
        "Original consumption preserved",
        event["consumed_by"] == "PROBE"
        and event["consumed_date"] == "2026-06-09",
    ))

    passed = 0

    for i, (name, ok) in enumerate(results, start=1):
        passed += int(ok)
        print(
            f"CASE {i}: {name:38} "
            f"| {'PASS' if ok else 'FAIL'}"
        )

    print("-" * 72)
    print(f"LEDGER RESULT: {passed}/{len(results)} PASS")



def run_readiness_tests():
    cases = [
        # current, fresh_lead, invalidated, expected

        # 1. Quiet market remains quiet
        ("QUIET", False, False, "QUIET"),

        # 2. Valid fresh lead arms the system
        ("QUIET", True,  False, "ARMED"),

        # 3. ARMED does not upgrade merely because time passes
        ("ARMED", False, False, "ARMED"),

        # 4. Another fresh lead does not change ARMED into deployment
        ("ARMED", True,  False, "ARMED"),

        # 5. Invalidation disarms the system
        ("ARMED", False, True,  "QUIET"),

        # 6. Invalidation has priority even if another lead is present
        ("ARMED", True,  True,  "QUIET"),
    ]

    print()
    print("=" * 72)
    print("READINESS LAYER v0.4 — ADVERSARIAL BLIND TEST")
    print("=" * 72)

    passed = 0

    for i, case in enumerate(cases, start=1):
        current, fresh, invalidated, expected = case

        actual = decide_readiness(
            current_readiness=current,
            valid_fresh_lead=fresh,
            lead_invalidated=invalidated,
        )

        ok = actual == expected
        passed += int(ok)

        print(
            f"CASE {i}: {current:5} "
            f"fresh={str(fresh):5} "
            f"invalidated={str(invalidated):5} "
            f"=> {actual:5} "
            f"| expected={expected:5} "
            f"| {'PASS' if ok else 'FAIL'}"
        )

    print("-" * 72)
    print(f"READINESS RESULT: {passed}/{len(cases)} PASS")


def run_probe_permission_tests():
    cases = [
        # readiness, invalidated, fresh, direction, unused, level, expected

        # 1. Not ARMED: no deployment permission
        ("QUIET", False, True,  "UP",   True,  3, False),

        # 2. ARMED but only continuation: no fresh evidence
        ("ARMED", False, False, "UP",   True,  3, False),

        # 3. ARMED + same-event continuation (L0)
        ("ARMED", False, True,  "UP",   True,  0, False),

        # 4. ARMED + same-subgroup confirmation (L1)
        ("ARMED", False, True,  "UP",   True,  1, False),

        # 5. ARMED + cross-subgroup fresh confirmation (L2)
        ("ARMED", False, True,  "UP",   True,  2, True),

        # 6. ARMED + cross-module fresh confirmation (L3)
        ("ARMED", False, True,  "UP",   True,  3, True),

        # 7. Independent but already consumed
        ("ARMED", False, True,  "UP",   False, 3, False),

        # 8. Independent but wrong direction
        ("ARMED", False, True,  "DOWN", True,  3, False),

        # 9. Invalidation overrides otherwise valid confirmation
        ("ARMED", True,  True,  "UP",   True,  3, False),
    ]

    print()
    print("=" * 72)
    print("PROBE PERMISSION v0.5 — ADVERSARIAL BLIND TEST")
    print("=" * 72)

    passed = 0

    for i, case in enumerate(cases, start=1):
        readiness, invalidated, fresh, direction, unused, level, expected = case

        actual = probe_permission(
            readiness=readiness,
            lead_invalidated=invalidated,
            confirmation_fresh=fresh,
            confirmation_direction=direction,
            confirmation_unused=unused,
            independence_level=level,
        )

        ok = actual == expected
        passed += int(ok)

        print(
            f"CASE {i}: {readiness:5} "
            f"fresh={str(fresh):5} "
            f"dir={direction:4} "
            f"unused={str(unused):5} "
            f"L{level} "
            f"=> {actual} | expected={expected} "
            f"| {'PASS' if ok else 'FAIL'}"
        )

    print("-" * 72)
    print(f"PERMISSION RESULT: {passed}/{len(cases)} PASS")


if __name__ == "__main__":
    run_blind_tests()
    run_evidence_identity_tests()
    run_consumption_ledger_tests()
    run_readiness_tests()
    run_probe_permission_tests()