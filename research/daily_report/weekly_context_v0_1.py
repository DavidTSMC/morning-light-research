from pathlib import Path
import pandas as pd

from research.moat15.standardize_m15_data import read_yfinance_raw

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw"

TICKERS = [
    "2059", "2330", "2382", "2454", "2603", "2882",
    "3017", "3583", "3661", "3665", "6472",
]


def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = df.resample("W-FRI").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Adj Close": "last",
        "Volume": "sum",
    })

    return weekly.dropna(
        subset=["Open", "High", "Low", "Close"]
    )

def completed_weekly(weekly, last_daily_date, *, as_of=None):
    # Production cutoff uses the Taipei calendar date. Friday becomes complete
    # on Saturday; a Friday run conservatively excludes that same Friday.
    # Keep the existing historical/replay behavior when as_of is omitted.
    if as_of is not None:
        return weekly[weekly.index < pd.Timestamp(as_of).normalize()]
    current_week_end = (
        pd.Timestamp(last_daily_date)
        .to_period("W-FRI")
        .end_time
        .normalize()
    )
    return weekly[weekly.index < current_week_end]

def main():
    print("MORNING LIGHT — WEEKLY CONTEXT v0.1")
    print("DATA BRIDGE AUDIT ONLY | NO INTERPRETATION")
    print("-" * 72)

    for ticker in TICKERS:
        path = RAW_DIR / f"{ticker}_TW.csv"

        df = read_yfinance_raw(path)
        weekly = to_weekly(df) 

        completed = completed_weekly(weekly, df.index[-1])
        developing = len(weekly) - len(completed)
        
        print(
            ticker,
            "| Daily:", len(df),
            "| Last Daily:", df.index[-1].date(),
            "| Weekly:", len(weekly),
            "| Completed:", len(completed),
            "| Developing:", developing, 
            "| Last W:", weekly.index[-1].date(),
        )


if __name__ == "__main__":
    main()
