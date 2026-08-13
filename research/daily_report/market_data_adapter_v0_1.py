import pandas as pd
import yfinance as yf


INSTRUMENTS = {
    "VIX": {
        "ticker": "^VIX",
        "label": "VIX",
        "unit": "",
        "decimals": 2,
    },
    "US10Y": {
        "ticker": "^TNX",
        "label": "US10Y",
        "unit": "%",
        "decimals": 3,
    },
    "DXY": {
        "ticker": "DX-Y.NYB",
        "label": "DXY",
        "unit": "",
        "decimals": 3,
    },
    "SOX": {
        "ticker": "^SOX",
        "label": "SOX",
        "unit": "",
        "decimals": 2,
    },
}


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def direction(current: float, previous: float, tolerance: float = 0.000001) -> str:
    change = current - previous

    if change > tolerance:
        return "↑"

    if change < -tolerance:
        return "↓"

    return "→"


def fetch_eod_snapshot(name: str, config: dict) -> dict:
    ticker = config["ticker"]

    df = yf.download(
        ticker,
        period="10d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df.empty:
        return {
            "name": name,
            "ticker": ticker,
            "status": "NO DATA",
        }

    df = flatten_columns(df)
    df = df.dropna(subset=["Close"])

    if len(df) < 2:
        return {
            "name": name,
            "ticker": ticker,
            "status": "INSUFFICIENT DATA",
        }

    current_row = df.iloc[-1]
    previous_row = df.iloc[-2]

    current = float(current_row["Close"])
    previous = float(previous_row["Close"])

    change = current - previous
    change_pct = (
        change / previous * 100
        if previous != 0
        else None
    )

    closes = df["Close"].astype(float)

    def horizon_direction(days: int) -> str:
        if len(closes) <= days:
            return "?"
        return direction(
            float(closes.iloc[-1]),
            float(closes.iloc[-1 - days]),
        )

    return {
        "name": name,
        "ticker": ticker,
        "status": "OK",
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "previous_as_of": df.index[-2].strftime("%Y-%m-%d"),
        "value": current,
        "previous": previous,
        "change": change,
        "change_pct": change_pct,
        "direction": direction(current, previous),
        "dir_1d": horizon_direction(1),
        "dir_3d": horizon_direction(3),
        "dir_5d": horizon_direction(5),
        "unit": config["unit"],
        "decimals": config["decimals"],
    }


def format_value(snapshot: dict) -> str:
    decimals = snapshot["decimals"]
    unit = snapshot["unit"]

    return f"{snapshot['value']:.{decimals}f}{unit}"


def main():
    print("=" * 78)
    print("MORNING LIGHT — GLOBAL EOD DATA ADAPTER v0.1")
    print("REAL DATA｜NO INTERPRETATION YET")
    print("=" * 78)

    snapshots = []

    for name, config in INSTRUMENTS.items():
        snapshot = fetch_eod_snapshot(
            name,
            config,
        )

        snapshots.append(snapshot)

        if snapshot["status"] != "OK":
            print(
                f"{name:<7} "
                f"{snapshot['status']}"
            )
            continue

        print(
            f"{name:<7} "
            f"{format_value(snapshot):>10} "
            f"{snapshot['change_pct']:+6.2f}%  "
            f"| 1D {snapshot['dir_1d']} "
            f"| 3D {snapshot['dir_3d']} "
            f"| 5D {snapshot['dir_5d']} "
            f"| as of {snapshot['as_of']}"
        )

    print("=" * 78)
    print("Guardrail: each instrument retains its own as-of date.")
    print("No macro state or trading conclusion is created yet.")
    print("=" * 78)

    return snapshots


if __name__ == "__main__":
    main()
