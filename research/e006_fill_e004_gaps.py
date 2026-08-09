from pathlib import Path
import csv


CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "episode_E004_evidence.csv"
)

# Snapshot-confirmed values only.
# MTM10 intentionally NOT filled yet:
# provenance of chart MA10 -> CSV MTM10 must be confirmed first.
PATCH = {
    "20:05": {
        "MTM3": "-0.02",
        "BBI": "64.12",
    },
    "20:15": {
        "MTM3": "0.01",
        "BBI": "64.12",
    },
    "20:25": {
        "MTM3": "-0.21",
        "BBI": "64.06",
    },
}


def main():
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changed = []

    for row in rows:
        time = row.get("time")

        if time not in PATCH:
            continue

        for field, value in PATCH[time].items():
            old_value = row.get(field, "")

            if old_value not in ("", None):
                raise ValueError(
                    f"Refusing overwrite: {time} {field} "
                    f"already contains {old_value}"
                )

            row[field] = value
            changed.append((time, field, value))

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("E006 - confirmed snapshot patch")
    for time, field, value in changed:
        print(f"{time} | {field:5} | {value}")

    print(f"patched cells: {len(changed)}")


if __name__ == "__main__":
    main()