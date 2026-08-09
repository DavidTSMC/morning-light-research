"""
Morning Light Research
E006 - Validation Case #1

Purpose
-------
Blind validation of the E005 timing-phase hypothesis.

Frozen hypothesis from E005 v0.7:
LEAD -> TURN -> RESONANCE -> BRIDGE -> CONFIRM

Validation outcomes allowed:
1. SUPPORTED
2. PARTIALLY SUPPORTED
3. NOT SUPPORTED

Principle:
Evidence first.
Do not modify the frozen phase hypothesis to fit E006.

Motto:
Research can be deep; answers must be concise.
Evidence can be abundant; conclusions must be honest.
"""

CASE = {
    "validation_id": "E006",
    "source_episode": "E004",
    "validation_type": "blind_validation",
    "hypothesis_source": "E005_v0.7",
}

FROZEN_PHASES = (
    "LEAD",
    "TURN",
    "RESONANCE",
    "BRIDGE",
    "CONFIRM",
)

from pathlib import Path
import csv


E004_EVIDENCE_PATH = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "episode_E004_evidence.csv"
)


def load_e004_evidence():
    rows = []

    with E004_EVIDENCE_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append(row)

    return rows


if __name__ == "__main__":
    evidence = load_e004_evidence()

    print("E006 - Validation Case #1")
    print(f"source episode : {CASE['source_episode']}")
    print(f"evidence rows  : {len(evidence)}")
    print(f"columns        : {list(evidence[0].keys()) if evidence else []}")
    print()
    print("=" * 72)
    print("E006 v0.1 - EVIDENCE INVENTORY")
    print("=" * 72)

    if evidence:
        print(f"first time     : {evidence[0].get('time')}")
        print(f"last time      : {evidence[-1].get('time')}")
        print()

        print("FIELD AVAILABILITY")

        for field in evidence[0].keys():
            available = sum(
                1
                for row in evidence
                if row.get(field) not in (None, "", "None")
            )

            print(
                f"{field:16} : "
                f"{available:2}/{len(evidence)}"
            )

        print()
    print("MISSING-TIME MAP")

    check_fields = ["MTM3", "MTM10", "BBI", "OBV", "OBV_MA3"]

    for field in check_fields:
        missing_times = [
            row.get("time")
            for row in evidence
            if row.get(field) in (None, "")
        ]

        print(
            f"{field:8} : "
            f"{missing_times if missing_times else 'COMPLETE'}"
        )

        print()
    print("MTM10 PROVENANCE CHECK")

    for row in evidence:
         if row.get("MTM10") not in (None, "", "None"):
            print(
                row.get("time"),
                "MTM3 =", row.get("MTM3"),
                "MTM10 =", row.get("MTM10"),
            )

            