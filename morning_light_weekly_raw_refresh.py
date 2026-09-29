"""Refresh the 11-stock raw daily files used by weekly_clinical_context.py.

Place this file in the morning-light-research repository root. Run from there:

    python morning_light_weekly_raw_refresh.py          # preview; no raw changes
    python morning_light_weekly_raw_refresh.py --apply  # backup, then replace

Requires pandas and yfinance. The existing project's read_yfinance_raw is used
to verify that every staged file can be read by the weekly calculation.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


TICKERS = ("2059", "2330", "2382", "2454", "2603", "2882", "3017", "3583", "3661", "3665", "6472")
FIELDS = ("Adj Close", "Close", "High", "Low", "Open", "Volume")
TAIPEI = ZoneInfo("Asia/Taipei")


def read_checked(path: Path) -> pd.DataFrame:
    from research.moat15.standardize_m15_data import read_yfinance_raw

    frame = read_yfinance_raw(path)
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError(f"Empty or unreadable data: {path}")
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index, errors="raise").tz_localize(None)
    needed = ("Open", "High", "Low", "Close", "Volume")
    missing = [name for name in needed if name not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns {missing}: {path}")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"Duplicate or unsorted dates: {path}")
    values = frame.loc[:, needed].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        raise ValueError(f"Missing or invalid OHLCV: {path}")
    if (values[["Open", "High", "Low", "Close"]] <= 0).any().any() or (values["Volume"] < 0).any():
        raise ValueError(f"Nonpositive price or negative volume: {path}")
    if (values["High"] < values[["Open", "Low", "Close"]].max(axis=1)).any():
        raise ValueError(f"High below OHLC: {path}")
    if (values["Low"] > values[["Open", "High", "Close"]].min(axis=1)).any():
        raise ValueError(f"Low above OHLC: {path}")
    return frame


def download_to_stage(symbol: str, first_date: pd.Timestamp, target: Path, today) -> None:
    import yfinance as yf

    fetched = yf.download(
        symbol,
        start=(first_date - pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
        end=(today + timedelta(days=1)).isoformat(),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if fetched is None or fetched.empty:
        raise ValueError(f"No data downloaded for {symbol}")
    if isinstance(fetched.columns, pd.MultiIndex):
        # yfinance normally returns Price/Ticker columns; normalize their order.
        if symbol in fetched.columns.get_level_values(0) and symbol not in fetched.columns.get_level_values(1):
            fetched = fetched.swaplevel(0, 1, axis=1)
        fetched.columns = fetched.columns.get_level_values(0)
    missing = [field for field in FIELDS if field not in fetched.columns]
    if missing:
        raise ValueError(f"Downloaded {symbol} is missing {missing}")
    fetched = fetched.loc[:, FIELDS].sort_index()
    fetched.index = pd.to_datetime(fetched.index).tz_localize(None)
    fetched.index.name = "Date"
    fetched.columns = pd.MultiIndex.from_product([FIELDS, [symbol]], names=["Price", "Ticker"])
    fetched.to_csv(target)


def compare(old: pd.DataFrame, fresh: pd.DataFrame, symbol: str, today) -> str:
    old_first, old_last = old.index[0], old.index[-1]
    new_first, new_last = fresh.index[0], fresh.index[-1]
    if new_first > old_first:
        raise ValueError(f"{symbol}: historical start would be lost ({old_first.date()} -> {new_first.date()})")
    if len(fresh) < len(old):
        raise ValueError(f"{symbol}: row count would shrink ({len(old)} -> {len(fresh)})")
    if new_last <= old_last:
        raise ValueError(f"{symbol}: no newer day ({old_last.date()} -> {new_last.date()})")
    if new_last.date() > today or (today - new_last.date()).days > 7:
        raise ValueError(f"{symbol}: latest date {new_last.date()} needs review")
    common = old.index.intersection(fresh.index)
    if len(common) < 5:
        raise ValueError(f"{symbol}: too few overlapping dates")
    before = pd.to_numeric(old.loc[common, "Close"], errors="raise")
    after = pd.to_numeric(fresh.loc[common, "Close"], errors="raise")
    relative_change = ((after - before).abs() / before).max()
    if relative_change > 0.01:
        raise ValueError(f"{symbol}: historical closes changed by up to {relative_change:.1%}; review source before applying")
    return f"{symbol}: {old_first.date()}..{old_last.date()} ({len(old)}) -> {new_first.date()}..{new_last.date()} ({len(fresh)})"


def refresh(root: Path, apply: bool) -> None:
    raw_dir = root / "data" / "raw"
    if not (root / "research" / "moat15" / "standardize_m15_data.py").exists():
        raise ValueError("Run from morning-light-research repository root")
    today = datetime.now(TAIPEI).date()
    timestamp = datetime.now(TAIPEI).strftime("%Y%m%d_%H%M%S")
    originals = {ticker: raw_dir / f"{ticker}_TW.csv" for ticker in TICKERS}
    missing = [str(path) for path in originals.values() if not path.is_file()]
    if missing:
        raise ValueError(f"Raw files missing; nothing changed: {missing}")

    # All 11 downloads and checks finish before the first original can change.
    with tempfile.TemporaryDirectory(prefix="ml_weekly_refresh_") as tmp:
        stage = Path(tmp)
        rows = []
        for ticker, original in originals.items():
            old = read_checked(original)
            proposed = stage / original.name
            download_to_stage(f"{ticker}.TW", old.index[0], proposed, today)
            fresh = read_checked(proposed)
            rows.append(compare(old, fresh, ticker, today))
        print("\n".join(rows))
        if not apply:
            print("PREVIEW ONLY: all 11 files passed; originals unchanged. Re-run with --apply to update.")
            return

        backup = root / "data" / "raw_backup" / timestamp
        backup.mkdir(parents=True, exist_ok=False)
        for ticker, original in originals.items():
            shutil.copy2(original, backup / original.name)
        replaced = []
        try:
            for ticker, original in originals.items():
                staged_copy = original.with_name(original.name + ".refresh_tmp")
                shutil.copy2(stage / original.name, staged_copy)
                os.replace(staged_copy, original)
                replaced.append(ticker)
        except Exception:
            for ticker in replaced:
                shutil.copy2(backup / originals[ticker].name, originals[ticker])
            raise
        finally:
            for original in originals.values():
                original.with_name(original.name + ".refresh_tmp").unlink(missing_ok=True)
        print(f"UPDATED 11 files. Backups: {backup}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="morning-light-research root")
    parser.add_argument("--apply", action="store_true", help="backup and replace after all checks pass")
    args = parser.parse_args()
    try:
        refresh(args.root.resolve(), args.apply)
        return 0
    except Exception as exc:
        print(f"STOPPED; check data before using weekly results: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
