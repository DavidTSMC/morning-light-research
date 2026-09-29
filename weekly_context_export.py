"""Export reviewed completed-week context from Morning Light Research.

Run in the morning-light-research root after refreshing the 11 raw daily CSVs.
This writes a candidate JSON only; it does not modify the mail repository.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from research.daily_report.weekly_clinical_context import TICKERS, build_watch_map


FIELDS = ("W Trend", "W Pulse", "W Loc", "Resonance")
ALLOWED = {
    "W Trend": {"↑多", "→轉", "↓弱"},
    "W Pulse": {"擴", "縮", "修", "弱"},
    "W Loc": {"低", "中", "高", "極"},
    "Resonance": {"◎齊", "○同", "△轉", "△錯", "※衝"},
}


def candidate() -> dict:
    raw = build_watch_map()
    expected = [str(ticker) for ticker in TICKERS]
    actual = [str(row["ticker"]) for row in raw]
    if len(expected) != 11 or actual != expected:
        raise ValueError(f"Ticker order mismatch: {actual}")

    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    weekly_dates = {date.fromisoformat(str(row["weekly_asof"])) for row in raw}
    daily_dates = {date.fromisoformat(str(row["daily_asof"])) for row in raw}
    if len(weekly_dates) != 1:
        raise ValueError(f"Weekly dates differ: {weekly_dates}")
    weekly_asof = weekly_dates.pop()
    if weekly_asof > today or (today - weekly_asof).days > 10:
        raise ValueError(f"Completed week is not recent: {weekly_asof}")
    if any(d < weekly_asof or d > today or (today - d).days > 7 for d in daily_dates):
        raise ValueError(f"Daily source dates need review: {daily_dates}")

    rows = []
    for ticker, row in zip(expected, raw):
        output = {"股票": ticker}
        for field in FIELDS:
            value = str(row[field])
            if value not in ALLOWED[field]:
                raise ValueError(f"{ticker}: unexpected {field}={value!r}")
            output[field] = value
        rows.append(output)
    return {
        "weekly_asof": weekly_asof.isoformat(),
        "source": "Morning Light Research completed-week calculation; candidate for review",
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("clinical_map_weekly_context_candidate.json"))
    args = parser.parse_args()
    payload = candidate()
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(f"Candidate: {args.output} | completed week: {payload['weekly_asof']} | rows: 11")
    print("Review before replacing the email repository's context JSON.")


if __name__ == "__main__":
    main()
