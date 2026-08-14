"""
MORNING LIGHT — E007
Event × Trading Clock Integration v0.1

Purpose:
Connect cross-market event classification
with actual follower trading-session time.

Constitution:
1. Event != State
2. Calendar day != Trading session
3. Market closed != Transmission failure
4. PENDING != NT
5. N/A != 0
6. Preserve actual calendar gap
"""
from e007_trading_clock_v0_1 import (
    next_tradable_session,
    classify_trading_lag,
)

from e007_cross_market_rulebook import classify_transmission

print("TRADING CLOCK IMPORT: PASS")
print("RULEBOOK IMPORT: PASS")

from datetime import date


# ------------------------------------------------------------
# E007 Integration Case 1
# Same-family bullish transmission on first follower session
# Expected: T+1 + EXACT
# ------------------------------------------------------------

leader_date = date(2026, 8, 10)

follower_sessions = [
    date(2026, 8, 11),
    date(2026, 8, 12),
    date(2026, 8, 13),
]

follower_event_date = date(2026, 8, 11)

lag_label = classify_trading_lag(
    leader_date,
    follower_event_date,
    follower_sessions,
)

lag_sessions = int(lag_label.split("+")[1])

classification = classify_transmission(
    "BULLISH",
    "WR",
    "BULLISH",
    "WR",
    lag_sessions,
)

print()
print("E007 INTEGRATION CASE 1")
print(f"Trading lag: {lag_label}")
print(f"Classification: {classification}")

if lag_label == "T+1" and classification == "EXACT":
    print("INTEGRATION CASE 1: PASS")
else:
    print("INTEGRATION CASE 1: FAIL")


   # ------------------------------------------------------------
# E007 Integration Case 2
# Calendar holiday gap, but first real follower session
# Expected: Calendar gap = 2 days, Trading lag = T+1, EXACT
# ------------------------------------------------------------

leader_date_2 = date(2026, 8, 10)

follower_sessions_2 = [
    date(2026, 8, 12),  # Aug 11: follower market closed
    date(2026, 8, 13),
    date(2026, 8, 14),
]

follower_event_date_2 = date(2026, 8, 12)

clock_result_2 = next_tradable_session(
    leader_date_2,
    follower_sessions_2,
)

lag_label_2 = classify_trading_lag(
    leader_date_2,
    follower_event_date_2,
    follower_sessions_2,
)

lag_sessions_2 = int(lag_label_2.split("+")[1])

classification_2 = classify_transmission(
    "BULLISH",
    "WR",
    "BULLISH",
    "WR",
    lag_sessions_2,
)

print()
print("E007 INTEGRATION CASE 2")
print(f"Calendar gap: {clock_result_2['calendar_gap']} days")
print(f"Trading lag: {lag_label_2}")
print(f"Classification: {classification_2}")

if (
    clock_result_2["calendar_gap"] == 2
    and lag_label_2 == "T+1"
    and classification_2 == "EXACT"
):
    print("INTEGRATION CASE 2: PASS")
else:
    print("INTEGRATION CASE 2: FAIL") 


# ------------------------------------------------------------
# E007 Integration Case 3
# Follower reacts on second real trading session
# and through another approved indicator family.
# Expected: T+2 + CASCADE
# ------------------------------------------------------------

leader_date_3 = date(2026, 8, 10)

follower_sessions_3 = [
    date(2026, 8, 11),
    date(2026, 8, 12),
    date(2026, 8, 13),
]

follower_event_date_3 = date(2026, 8, 12)

lag_label_3 = classify_trading_lag(
    leader_date_3,
    follower_event_date_3,
    follower_sessions_3,
)

lag_sessions_3 = int(lag_label_3.split("+")[1])

classification_3 = classify_transmission(
    "BULLISH",
    "WR",
    "BULLISH",
    "BIAS",
    lag_sessions_3,
)

print()
print("E007 INTEGRATION CASE 3")
print(f"Trading lag: {lag_label_3}")
print(f"Classification: {classification_3}")

if (
    lag_label_3 == "T+2"
    and classification_3 == "CASCADE"
):
    print("INTEGRATION CASE 3: PASS")
else:
    print("INTEGRATION CASE 3: FAIL")


# ------------------------------------------------------------
# E007 Integration Case 4
# Future follower session is not available yet.
# Expected: PENDING, and Rulebook must NOT classify as NT.
# ------------------------------------------------------------

leader_date_4 = date(2026, 8, 14)

follower_sessions_4 = []

clock_result_4 = next_tradable_session(
    leader_date_4,
    follower_sessions_4,
)

if clock_result_4["status"] == "PENDING":
    integration_status_4 = "PENDING"
    classification_4 = None
else:
    integration_status_4 = "READY"
    classification_4 = classify_transmission(
        "BULLISH",
        "WR",
        None,
        None,
        None,
    )

print()
print("E007 INTEGRATION CASE 4")
print(f"Clock status: {clock_result_4['status']}")
print(f"Integration status: {integration_status_4}")
print(f"Classification: {classification_4}")

if (
    clock_result_4["status"] == "PENDING"
    and integration_status_4 == "PENDING"
    and classification_4 is None
):
    print("INTEGRATION CASE 4: PASS")
else:
    print("INTEGRATION CASE 4: FAIL")


# ------------------------------------------------------------
# E007 Integration Case 5
# Observation window completed with no follower event.
# Expected: NT, not PENDING.
# ------------------------------------------------------------

leader_date_5 = date(2026, 8, 10)

follower_sessions_5 = [
    date(2026, 8, 11),  # T+1
    date(2026, 8, 12),  # T+2
]

# No follower event occurred during the valid T+0 ~ T+2 window.
follower_event_date_5 = None

if follower_event_date_5 is None:
    integration_status_5 = "READY"
    classification_5 = classify_transmission(
        "BULLISH",
        "WR",
        None,
        None,
        2,
    )
else:
    integration_status_5 = "EVENT_FOUND"
    classification_5 = None

print()
print("E007 INTEGRATION CASE 5")
print(f"Observation window: T+0 to T+2")
print(f"Integration status: {integration_status_5}")
print(f"Classification: {classification_5}")

if (
    integration_status_5 == "READY"
    and classification_5 == "NT"
):
    print("INTEGRATION CASE 5: PASS")
else:
    print("INTEGRATION CASE 5: FAIL")




