"""Build weekly context in isolation from the committed 11-stock seeds.

python weekly_pipeline.py --offline  # local regression; no network
python weekly_pipeline.py            # fetch completed daily bars and validate
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from morning_light_weekly_raw_refresh import TICKERS, read_checked, refresh
from weekly_context_export import candidate


def run(root: Path, output: Path, offline: bool) -> dict:
    sources = [root / "data/weekly_seed" / f"{t}_TW.csv" for t in TICKERS]
    for source in sources:
        read_checked(source)
    with tempfile.TemporaryDirectory(prefix="morning_light_weekly_") as directory:
        stage = Path(directory)
        raw = stage / "data/raw"
        raw.mkdir(parents=True)
        reader = Path("research/moat15/standardize_m15_data.py")
        (stage / reader).parent.mkdir(parents=True)
        shutil.copy2(root / reader, stage / reader)
        for source in sources:
            shutil.copy2(source, raw / source.name)
        previous = Path.cwd()
        try:
            os.chdir(stage)
            if not offline:
                refresh(stage, apply=True)
            payload = candidate()
            audit = {
                "generated_at": datetime.now(ZoneInfo("Asia/Taipei")).isoformat(),
                "mode": "offline seed regression" if offline else "downloaded completed daily bars",
                "weekly_asof": payload["weekly_asof"],
                "rows": [],
            }
            for ticker, seed in zip(TICKERS, sources):
                path = raw / seed.name
                frame = read_checked(path)
                audit["rows"].append({
                    "ticker": ticker, "rows": len(frame),
                    "first_date": str(frame.index[0].date()),
                    "last_date": str(frame.index[-1].date()),
                    "seed_sha256": hashlib.sha256(seed.read_bytes()).hexdigest(),
                    "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                })
            # All downloads, evidence, and date checks finish before output.
            output.mkdir(parents=True, exist_ok=True)
            preserved = output / "sources"
            preserved.mkdir(exist_ok=True)
            for source in sources:
                shutil.copy2(raw / source.name, preserved / source.name)
            for name, value in (("clinical_map_weekly_context_candidate.json", payload), ("audit.json", audit)):
                temporary = output / (name + ".tmp")
                temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                os.replace(temporary, output / name)
            print(f"VALIDATED | completed week {payload['weekly_asof']} | 11 stocks | {output}")
            for row in payload["rows"]:
                print(row["股票"], row["W Trend"], row["W Pulse"], row["W Loc"], row["Resonance"])
            return payload
        finally:
            os.chdir(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("outputs/weekly_job"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    run(root, args.output.resolve(), args.offline)


if __name__ == "__main__":
    main()
