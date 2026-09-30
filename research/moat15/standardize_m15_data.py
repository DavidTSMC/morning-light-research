from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
UNIVERSE = ROOT / "research/moat15/universe.csv"
RAW_DIR = ROOT / "data/raw"
OUT_DIR = ROOT / "research/moat15/processed"

REQUIRED = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

def read_yfinance_raw(path):
    # yfinance MultiIndex CSV:
    # row 1 = Price
    # row 2 = Ticker
    # row 3 = Date
    df = pd.read_csv(path, header=[0, 1], index_col=0)

    # Keep price-field level only.
    df.columns = df.columns.get_level_values(0)

    df.index = pd.to_datetime(df.index, errors="coerce")
    df.index.name = "Date"

    df = df[~df.index.isna()].copy()
    df = df.sort_index()

    return df

def audit(df, ticker):
    problems = []

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        problems.append(f"missing_columns={missing_cols}")
        return problems

    if df.index.duplicated().any():
        problems.append(
            f"duplicate_dates={int(df.index.duplicated().sum())}"
        )

    missing_values = int(df[REQUIRED].isna().sum().sum())
    if missing_values:
        problems.append(f"missing_ohlcv={missing_values}")

    numeric = df[REQUIRED].apply(pd.to_numeric, errors="coerce")

    bad_numeric = int(numeric.isna().sum().sum())
    if bad_numeric:
        problems.append(f"nonnumeric_ohlcv={bad_numeric}")

    bad_hl = int((numeric["High"] < numeric["Low"]).sum())
    if bad_hl:
        problems.append(f"high_below_low={bad_hl}")

    bad_open = int(
        (
            (numeric["Open"] > numeric["High"]) |
            (numeric["Open"] < numeric["Low"])
        ).sum()
    )
    if bad_open:
        problems.append(f"open_outside_range={bad_open}")

    bad_close = int(
        (
            (numeric["Close"] > numeric["High"]) |
            (numeric["Close"] < numeric["Low"])
        ).sum()
    )
    if bad_close:
        problems.append(f"close_outside_range={bad_close}")

    bad_volume = int((numeric["Volume"] < 0).sum())
    if bad_volume:
        problems.append(f"negative_volume={bad_volume}")

    return problems

def main():
    universe = pd.read_csv(UNIVERSE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pass_count = 0
    fail_count = 0

    print("M15 DATA INTEGRITY GATE")
    print("=" * 95)

    for _, row in universe.iterrows():
        ticker = row["ticker"]
        name = row["name"]

        raw_path = RAW_DIR / f"{ticker.replace('.', '_')}.csv"

        if not raw_path.exists():
            print(f"FAIL {ticker:<9} {name:<8} raw file missing")
            fail_count += 1
            continue

        try:
            df = read_yfinance_raw(raw_path)
            problems = audit(df, ticker)

            if problems:
                print(
                    f"FAIL {ticker:<9} {name:<8} "
                    + " | ".join(problems)
                )
                fail_count += 1
                continue

            out = df[REQUIRED].copy()
            out.to_csv(
                OUT_DIR / f"{ticker.replace('.', '_')}.csv"
            )

            print(
                f"PASS {ticker:<9} {name:<8} "
                f"rows={len(out):4d} "
                f"{out.index.min().date()} -> {out.index.max().date()}"
            )

            pass_count += 1

        except Exception as e:
            print(f"FAIL {ticker:<9} {name:<8} ERROR={e}")
            fail_count += 1

    print("=" * 95)
    print(f"PASS: {pass_count}/15")
    print(f"FAIL: {fail_count}/15")

    if pass_count == 15 and fail_count == 0:
        print("\nM15 DATA INTEGRITY GATE: PASS")
    else:
        print("\nM15 DATA INTEGRITY GATE: HOLD")

if __name__ == "__main__":
    main()
