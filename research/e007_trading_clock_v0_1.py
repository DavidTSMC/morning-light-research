from datetime import date


def next_tradable_session(leader_date, follower_sessions):
    """
    Find the first actual follower trading session
    strictly after the leader event date.
    """
    future_sessions = sorted(
        d for d in follower_sessions if d > leader_date
    )

    if not future_sessions:
        return {
            "status": "PENDING",
            "next_session": None,
            "calendar_gap": None,
        }

    next_session = future_sessions[0]

    return {
        "status": "READY",
        "next_session": next_session,
        "calendar_gap": (next_session - leader_date).days,
    }


def classify_trading_lag(
    leader_date,
    follower_event_date,
    follower_sessions,
):
    """
    T+1 means first actual follower trading session,
    not leader date + 1 calendar day.
    """
    sessions = sorted(
        d for d in follower_sessions if d > leader_date
    )

    if follower_event_date is None:
        return "NT"

    if follower_event_date not in sessions:
        return "INVALID_SESSION"

    position = sessions.index(follower_event_date) + 1
    return f"T+{position}"


tests = []

# 1. Normal next-day market session
leader = date(2026, 8, 10)
sessions = [
    date(2026, 8, 11),
    date(2026, 8, 12),
]
r = next_tradable_session(leader, sessions)
tests.append((
    "Normal next day",
    r["next_session"] == date(2026, 8, 11)
    and r["calendar_gap"] == 1,
))

# 2. Follower market holiday
leader = date(2026, 8, 10)
sessions = [
    date(2026, 8, 12),
    date(2026, 8, 13),
]
r = next_tradable_session(leader, sessions)
tests.append((
    "Follower holiday",
    r["next_session"] == date(2026, 8, 12)
    and r["calendar_gap"] == 2,
))

# 3. Weekend gap
leader = date(2026, 8, 14)
sessions = [
    date(2026, 8, 17),
    date(2026, 8, 18),
]
r = next_tradable_session(leader, sessions)
tests.append((
    "Weekend gap",
    r["next_session"] == date(2026, 8, 17)
    and r["calendar_gap"] == 3,
))

# 4. No future follower session yet
leader = date(2026, 8, 14)
r = next_tradable_session(leader, [])
tests.append((
    "Future session unavailable",
    r["status"] == "PENDING"
    and r["next_session"] is None,
))

# 5. Event occurs on second real trading session
leader = date(2026, 8, 10)
sessions = [
    date(2026, 8, 12),
    date(2026, 8, 13),
    date(2026, 8, 14),
]
lag = classify_trading_lag(
    leader,
    date(2026, 8, 13),
    sessions,
)
tests.append((
    "Trading lag T+2",
    lag == "T+2",
))


print("=" * 72)
print("MORNING LIGHT — E007 TRADING CLOCK v0.1")
print("=" * 72)

passed = 0

for name, ok in tests:
    status = "PASS" if ok else "FAIL"
    print(f"{name:<30} {status}")
    if ok:
        passed += 1

print()
print(f"Tests passed: {passed}/{len(tests)}")

if passed == len(tests):
    print("TRADING CLOCK VALIDATION: PASS")
else:
    print("TRADING CLOCK VALIDATION: FAIL")

print("=" * 72)
print("RULE: Calendar day != Trading session")
print("RULE: Market closed != Transmission failure")
print("RULE: N/A != 0")
print("RULE: Preserve actual calendar gap")