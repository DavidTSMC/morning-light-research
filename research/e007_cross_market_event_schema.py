from dataclasses import dataclass, asdict
from typing import Optional, Literal
import json


# ============================================================
# MORNING LIGHT — E007
# Cross-Market Event Record Schema v0.1
#
# PURPOSE
# -------
# One row / object = ONE confirmed or provisional technical event.
#
# Core principle:
#   Position != Event
#   State != Cross
#   Event date must be traceable
# ============================================================


Market = Literal[
    "US_ADR",
    "TW_CASH",
    "TW_FUTURES",
    "GOLD",
    "CRYPTO",
    "OTHER",
]

Direction = Literal[
    "BULLISH",
    "BEARISH",
]

EventType = Literal[
    "CROSS_UP",
    "CROSS_DOWN",
    "V_TURN",
    "A_TURN",
    "OTHER",
]

Confirmation = Literal[
    "PROVISIONAL",
    "EOD_CONFIRMED",
]

TransmissionType = Literal[
    "EXACT",
    "CASCADE",
    "NONE",
]


@dataclass(frozen=True)
class TechnicalEvent:
    # ----------------------------
    # Identity
    # ----------------------------
    event_id: str
    pair_id: str

    market: Market
    ticker: str
    session_date: str

    # ----------------------------
    # Signal identity
    # ----------------------------
    indicator_family: str
    indicator_name: str

    direction: Direction
    event_type: EventType

    # ----------------------------
    # Timing / Visual Grammar
    # ----------------------------
    cross_age: int
    confirmation: Confirmation

    # ----------------------------
    # Evidence
    # ----------------------------
    value: Optional[float] = None
    reference_value: Optional[float] = None

    # ----------------------------
    # Optional audit fields
    # ----------------------------
    source: Optional[str] = None
    note: Optional[str] = None


def validate_event(event: TechnicalEvent) -> None:
    """
    Raise ValueError if the event violates core E007 rules.
    """

    if event.cross_age < 0:
        raise ValueError("cross_age must be >= 0")

    # A true new event must have age 0.
    if event.event_type in {
        "CROSS_UP",
        "CROSS_DOWN",
        "V_TURN",
        "A_TURN",
    } and event.cross_age != 0:
        raise ValueError(
            "A newly recorded technical event must have cross_age = 0. "
            "Older states are not new events."
        )

    if not event.event_id.strip():
        raise ValueError("event_id cannot be empty")

    if not event.pair_id.strip():
        raise ValueError("pair_id cannot be empty")

    if not event.ticker.strip():
        raise ValueError("ticker cannot be empty")

    if not event.indicator_family.strip():
        raise ValueError("indicator_family cannot be empty")


def event_to_dict(event: TechnicalEvent) -> dict:
    validate_event(event)
    return asdict(event)


def event_to_json(event: TechnicalEvent) -> str:
    return json.dumps(
        event_to_dict(event),
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# EXAMPLE EVENTS
# These are schema examples only.
# They do NOT claim historical validation.
# ============================================================

if __name__ == "__main__":

    example_adr = TechnicalEvent(
        event_id="TSM_2026XXXX_WR_UP",
        pair_id="TSM_2330",
        market="US_ADR",
        ticker="TSM",
        session_date="2026-XX-XX",
        indicator_family="WR",
        indicator_name="WR3_WR5",
        direction="BULLISH",
        event_type="CROSS_UP",
        cross_age=0,
        confirmation="EOD_CONFIRMED",
        value=None,
        reference_value=None,
        source="research_example",
        note="Schema example only — not a validated historical event.",
    )

    example_tw = TechnicalEvent(
        event_id="2330_2026XXXX_BIAS3_UP",
        pair_id="TSM_2330",
        market="TW_CASH",
        ticker="2330",
        session_date="2026-XX-XX",
        indicator_family="BIAS",
        indicator_name="BIAS3",
        direction="BULLISH",
        event_type="CROSS_UP",
        cross_age=0,
        confirmation="EOD_CONFIRMED",
        value=None,
        reference_value=0.0,
        source="research_example",
        note="Possible follower event example only.",
    )

    print("=" * 72)
    print("MORNING LIGHT — E007 EVENT SCHEMA v0.1")
    print("=" * 72)

    print()
    print("ADR example:")
    print(event_to_json(example_adr))

    print()
    print("TW example:")
    print(event_to_json(example_tw))

    print()
    print("=" * 72)
    print("SCHEMA VALIDATION: PASS")
    print("=" * 72)
