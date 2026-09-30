import hashlib
import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from morning_light_weekly_raw_refresh import compare
from research.daily_report.weekly_context_v0_1 import completed_weekly
from weekly_pipeline import run


ROOT = Path(__file__).resolve().parents[1]


class FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 30, 9, 30, tzinfo=tz)


class WeeklyScheduleTests(unittest.TestCase):
    def test_friday_excludes_developing_week(self):
        frame = pd.DataFrame({"Close": [1, 2]}, index=pd.to_datetime(["2026-09-18", "2026-09-25"]))
        result = completed_weekly(frame, date(2026, 9, 25), as_of=date(2026, 9, 25))
        self.assertEqual(str(result.index[-1].date()), "2026-09-18")

    def test_saturday_includes_just_completed_friday(self):
        frame = pd.DataFrame({"Close": [1, 2]}, index=pd.to_datetime(["2026-09-18", "2026-09-25"]))
        result = completed_weekly(frame, date(2026, 9, 25), as_of=date(2026, 9, 26))
        self.assertEqual(str(result.index[-1].date()), "2026-09-25")

    def test_legacy_replay_cutoff_is_preserved(self):
        frame = pd.DataFrame({"Close": [1, 2]}, index=pd.to_datetime(["2026-09-18", "2026-09-25"]))
        result = completed_weekly(frame, date(2026, 9, 25))
        self.assertEqual(str(result.index[-1].date()), "2026-09-18")

    def test_same_latest_session_is_valid_idempotent_refresh(self):
        frame = pd.DataFrame({"Close": [100.] * 6}, index=pd.bdate_range("2026-09-22", periods=6))
        compare(frame, frame.copy(), "test", date(2026, 9, 30))

    def test_latest_session_regression_stops(self):
        frame = pd.DataFrame({"Close": [100.] * 6}, index=pd.bdate_range("2026-09-22", periods=6))
        with self.assertRaises(ValueError):
            compare(frame, frame.iloc[:-1], "test", date(2026, 9, 30))

    def test_historical_price_drift_stops(self):
        frame = pd.DataFrame({"Close": [100.] * 6}, index=pd.bdate_range("2026-09-22", periods=6))
        changed = frame.copy()
        changed.iloc[0, 0] = 102.
        with self.assertRaisesRegex(ValueError, "historical closes"):
            compare(frame, changed, "test", date(2026, 9, 30))

    def test_offline_pipeline_matches_reviewed_11_and_preserves_raw(self):
        with tempfile.TemporaryDirectory() as directory, patch("weekly_context_export.datetime", FrozenClock):
            output = Path(directory) / "output"
            raw = ROOT / "data/raw"
            before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.glob("*_TW.csv")}
            payload = run(ROOT, output, offline=True)
            expected = [
                ("2059", "→轉", "縮", "低", "△錯"), ("2330", "↑多", "修", "中", "○同"),
                ("2382", "→轉", "修", "中", "△錯"), ("2454", "↑多", "擴", "極", "△錯"),
                ("2603", "↑多", "縮", "中", "△轉"), ("2882", "→轉", "縮", "中", "△轉"),
                ("3017", "→轉", "縮", "極", "△轉"), ("3583", "→轉", "修", "中", "△轉"),
                ("3661", "→轉", "修", "中", "△轉"), ("3665", "↑多", "修", "中", "○同"),
                ("6472", "→轉", "縮", "低", "◎齊"),
            ]
            fields = ["股票", "W Trend", "W Pulse", "W Loc", "Resonance"]
            self.assertEqual([tuple(r[f] for f in fields) for r in payload["rows"]], expected)
            self.assertEqual(payload["weekly_asof"], "2026-09-25")
            self.assertEqual(len(json.loads((output / "audit.json").read_text())["rows"]), 11)
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.glob("*_TW.csv")}
            self.assertEqual(before, after)

    def test_stale_seed_cannot_generate_next_weeks_output(self):
        class LaterClock(FrozenClock):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 4, 9, 30, tzinfo=tz)
        with tempfile.TemporaryDirectory() as directory, patch("weekly_context_export.datetime", LaterClock):
            output = Path(directory) / "output"
            with self.assertRaisesRegex(ValueError, "Need completed week|Daily source dates need review"):
                run(ROOT, output, offline=True)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
