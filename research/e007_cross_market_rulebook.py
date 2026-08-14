"""
MORNING LIGHT — E007
Cross-Market Lead–Lag Rulebook v0.1

PURPOSE
-------
Freeze the research rules BEFORE historical validation.

Core principle:
    Define the exam before seeing the score.
"""

# ============================================================
# RULE 1 — LEAD WINDOW
# ============================================================

LEAD_WINDOW = {
    "T+0": 0,
    "T+1": 1,
    "T+2": 2,
}

MAX_LEAD_SESSIONS = 2

NO_TRANSMISSION = "NT"
FALSE_LEAD = "FL"


# ============================================================
# RULE 2 — TRANSMISSION TYPE
# ============================================================

TRANSMISSION_EXACT = "EXACT"
TRANSMISSION_CASCADE = "CASCADE"

# EXACT:
# Same direction + same indicator family.
#
# Example:
# TSM W/R bullish event
#   -> 2330 W/R bullish event
#
# CASCADE:
# Same direction + different approved timing family.
#
# Example:
# TSM W/R bullish event
#   -> 2330 J bullish event
#   -> 2330 Bias bullish event


# ============================================================
# RULE 3 — APPROVED TIMING FAMILIES
# ============================================================

APPROVED_FAMILIES = (
    "WR",
    "J",
    "BIAS",
    "MTM",
    "DI_OSC",
)


# ============================================================
# RULE 4 — DIRECTION MATCHING
# ============================================================

BULLISH = "BULLISH"
BEARISH = "BEARISH"

DIRECTIONS = (
    BULLISH,
    BEARISH,
)

# Machine interpretation:
#
# WR:
#   bullish = WR3 crosses above WR5
#   bearish = WR3 crosses below WR5
#
# J:
#   bullish = confirmed V-turn
#   bearish = confirmed A-turn
#
# BIAS:
#   bullish = Bias3 crosses above 0
#   bearish = Bias3 crosses below 0
#
# MTM:
#   bullish = MTM3 crosses above 0
#   bearish = MTM3 crosses below 0
#
# DI_OSC:
#   bullish = DI Osc crosses above 0
#   bearish = DI Osc crosses below 0


# ============================================================
# RULE 5 — EVENT != STATE
# ============================================================

EVENT_AGE_AT_CREATION = 0

# IMPORTANT:
#
# Bias3 > 0 today does NOT mean a bullish event happened today.
#
# A bullish Bias event requires:
#   yesterday Bias3 <= 0
#   AND
#   today Bias3 > 0
#
# Same principle applies to all cross-based families.
#
# Old events must NOT be counted again on subsequent days.


# ============================================================
# RULE 6 — CONFIRMATION
# ============================================================

PROVISIONAL = "PROVISIONAL"
EOD_CONFIRMED = "EOD_CONFIRMED"

# E007 historical validation uses EOD_CONFIRMED events
# unless a future experiment explicitly studies intraday timing.

VALIDATION_CONFIRMATION = EOD_CONFIRMED


# ============================================================
# RULE 7 — FIRST VALIDATION PAIRS
# ============================================================

VALIDATION_PAIRS = {
    "TSM_2330": {
        "leader": "TSM",
        "follower": "2330",
    },
    "ASX_3711": {
        "leader": "ASX",
        "follower": "3711",
    },
    "UMC_2303": {
        "leader": "UMC",
        "follower": "2303",
    },
}


# ============================================================
# RULE 8 — CLASSIFICATION
# ============================================================

def classify_transmission(
    leader_direction,
    leader_family,
    follower_direction=None,
    follower_family=None,
    lag_sessions=None,
):
    """
    Classify one leader event against one follower outcome.

    Returns:
        EXACT
        CASCADE
        NT
        FL
    """

    if follower_direction is None:
        return NO_TRANSMISSION

    if lag_sessions is None:
        return NO_TRANSMISSION

    if lag_sessions < 0 or lag_sessions > MAX_LEAD_SESSIONS:
        return NO_TRANSMISSION

    if follower_direction != leader_direction:
        return FALSE_LEAD

    if follower_family == leader_family:
        return TRANSMISSION_EXACT

    if (
        leader_family in APPROVED_FAMILIES
        and follower_family in APPROVED_FAMILIES
    ):
        return TRANSMISSION_CASCADE

    return NO_TRANSMISSION


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        (
            "Exact bullish",
            classify_transmission(
                "BULLISH", "WR",
                "BULLISH", "WR",
                1,
            ),
            "EXACT",
        ),
        (
            "Cascade bullish",
            classify_transmission(
                "BULLISH", "WR",
                "BULLISH", "BIAS",
                1,
            ),
            "CASCADE",
        ),
        (
            "False lead",
            classify_transmission(
                "BULLISH", "WR",
                "BEARISH", "WR",
                1,
            ),
            "FL",
        ),
        (
            "Too late",
            classify_transmission(
                "BULLISH", "WR",
                "BULLISH", "WR",
                3,
            ),
            "NT",
        ),
        (
            "No follower event",
            classify_transmission(
                "BEARISH", "J",
                None, None,
                None,
            ),
            "NT",
        ),
    ]

    print("=" * 72)
    print("MORNING LIGHT — E007 RULEBOOK v0.1")
    print("=" * 72)

    passed = 0

    for name, actual, expected in tests:

        ok = actual == expected

        print(
            f"{name:<24} "
            f"actual={actual:<8} "
            f"expected={expected:<8} "
            f"{'PASS' if ok else 'FAIL'}"
        )

        passed += int(ok)

    print()
    print(f"Tests passed: {passed}/{len(tests)}")

    if passed != len(tests):
        raise SystemExit("RULEBOOK VALIDATION: FAIL")

    print("RULEBOOK VALIDATION: PASS")
    print("=" * 72)
