from pathlib import Path
import pandas as pd

from research.moat15.standardize_m15_data import read_yfinance_raw
from research.daily_report.weekly_context_v0_1 import (
    to_weekly,
    completed_weekly,
)
from engine.indicator_engine import build_indicators
from indicators.mtm import calculate_mtm
from indicators.wr import calculate_wr


TICKERS = [
    "2059", "2330", "2382", "2454", "2603", "2882",
    "3017", "3583", "3661", "3665", "6472",
]


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Morning Light direction, pulse, and location evidence.

    Same anatomy, different clock:
    the meaning of the period comes from the input timeframe.
    """
    x = build_indicators(df.copy())

    close = df["Close"].astype(float)

    x["MTM3"] = calculate_mtm(df, period=3)
    x["Bias3"] = (
        close / close.rolling(3).mean() - 1.0
    ) * 100.0

    x["WR3"] = calculate_wr(df, period=3)
    x["R5"] = close.pct_change(5) * 100.0

    d_line = (
        close.ewm(span=12, adjust=False).mean()
        - close.ewm(span=26, adjust=False).mean()
    )
    m_line = d_line.ewm(span=9, adjust=False).mean()

    x["DM"] = d_line - m_line
    x["dDM"] = x["DM"].diff()

    return x


def trend_label(r) -> str:
    """
    Formal Weekly Trend candidate.

    Direction only.
    Does not use location or runway.
    """
    if (
        r["DMI_OSC"] < 0
        and r["Bias3"] < 0
        and r["MTM3"] < 0
    ):
        return "↓弱"

    if (
        r["DMI_OSC"] > 0
        and r["Bias3"] >= 0
        and r["MTM3"] >= 0
    ):
        return "↑多"

    return "→轉"


def pulse_label(r) -> str:
    """
    Weekly Pulse presentation layer.

    正↑ -> 擴
    正↓ -> 縮
    負↑ -> 修
    負↓ -> 弱

    Pulse is velocity / persistence, not direction.
    """
    dm = r["DM"]
    ddm = r["dDM"]

    if dm >= 0 and ddm >= 0:
        return "擴"

    if dm >= 0 and ddm < 0:
        return "縮"

    if dm < 0 and ddm >= 0:
        return "修"

    return "弱"


def direction_state(r) -> str:
    """
    Conservative directional state for R/A comparison.
    """
    if r["DMI_OSC"] > 0 and r["MTM3"] >= 0:
        return "UP"

    if r["DMI_OSC"] < 0 and r["MTM3"] < 0:
        return "DOWN"

    return "MIX"


def resonance_alignment_label(dr, wr) -> str:
    """
    R/A v0.2

    ◎齊 = direction + phase aligned
    ○同 = same direction, phase incomplete
    △轉 = transition / partial / unresolved
    △錯 = phase divergence / misalignment
    ×衝 = genuine opposite formal directions
    """
    ddir = direction_state(dr)
    wdir = direction_state(wr)

    d_level = 1 if dr["DM"] >= 0 else -1
    w_level = 1 if wr["DM"] >= 0 else -1

    d_move = 1 if dr["dDM"] >= 0 else -1
    w_move = 1 if wr["dDM"] >= 0 else -1

    if (
        ddir in ("UP", "DOWN")
        and wdir in ("UP", "DOWN")
        and ddir != wdir
    ):
        return "×衝"

    if ddir == wdir and ddir in ("UP", "DOWN"):
        if d_level == w_level and d_move == w_move:
            return "◎齊"
        return "○同"

    if d_move != w_move:
        return "△錯"

    return "△轉"


def build_r5_location_thresholds(
    tickers=TICKERS,
) -> dict:
    """
    Build common pooled R5 thresholds from Completed Weeks only.

    W Loc is POSITION FACT ONLY.
    It is not runway and not forecast.
    """
    rows = []

    for ticker in tickers:
        path = Path(f"data/raw/{ticker}_TW.csv")
        daily = read_yfinance_raw(path)

        weekly = to_weekly(daily)
        completed = completed_weekly(
            weekly,
            daily.index[-1]
        ).copy()

        close = completed["Close"].astype(float)
        r5 = close.pct_change(5) * 100.0

        rows.append(
            pd.DataFrame({"R5": r5}).dropna()
        )

    pool = pd.concat(rows, ignore_index=True)

    return {
        "P25": float(pool["R5"].quantile(0.25)),
        "P75": float(pool["R5"].quantile(0.75)),
        "P90": float(pool["R5"].quantile(0.90)),
    }


def location_label(r, thresholds: dict) -> str:
    """
    Weekly location only.

    LOW / MID / HIGH / EXTREME -> 低 / 中 / 高 / 極

    Does NOT imply good/bad.
    Does NOT imply runway.
    """
    r5 = r["R5"]

    if r5 >= thresholds["P90"]:
        return "極"

    if r5 >= thresholds["P75"]:
        return "高"

    if r5 <= thresholds["P25"]:
        return "低"

    return "中"


def build_weekly_clinical_context(
    ticker: str,
    thresholds: dict | None = None,
) -> dict:
    """
    Build final Weekly Clinical Context for one ticker.

    Formal Weekly fields use Completed Weeks only.
    Developing Week is excluded from formal structure.
    """
    path = Path(f"data/raw/{ticker}_TW.csv")
    daily = read_yfinance_raw(path)

    d = enrich(daily)
    dr = d.iloc[-1]

    weekly = to_weekly(daily)
    completed = completed_weekly(
        weekly,
        daily.index[-1]
    ).copy()

    w = enrich(completed)
    wr = w.iloc[-1]

    if thresholds is None:
        thresholds = build_r5_location_thresholds()

    return {
        "ticker": ticker,
        "daily_asof": daily.index[-1].strftime("%Y-%m-%d"),
        "weekly_asof": completed.index[-1].strftime("%Y-%m-%d"),
        "W Trend": trend_label(wr),
        "W Pulse": pulse_label(wr),
        "W Loc": location_label(wr, thresholds),
        "Resonance": resonance_alignment_label(dr, wr),
    }


def build_watch_map(
    tickers=TICKERS,
) -> list[dict]:
    """
    Build 11-stock rehearsal / regression output.
    """
    thresholds = build_r5_location_thresholds(tickers)

    return [
        build_weekly_clinical_context(
            ticker,
            thresholds=thresholds,
        )
        for ticker in tickers
    ]


if __name__ == "__main__":
    print("MORNING LIGHT — WEEKLY CLINICAL CONTEXT v0.1")
    print("COMPLETED WEEK ONLY | NO ACTION")
    print("=" * 72)

    rows = build_watch_map()

    for r in rows:
        print(
            f"{r['ticker']:<5} | "
            f"W Trend {r['W Trend']:<3} | "
            f"W Pulse {r['W Pulse']:<2} | "
            f"W Loc {r['W Loc']:<1} | "
            f"R/A {r['Resonance']:<2} | "
            f"W asof {r['weekly_asof']}"
        )

    print("=" * 72)
    print("W Loc = POSITION FACT ONLY; NOT RUNWAY / NOT FORECAST.")
    print("NO SCORE / NO RANK / NO ACTION / NO EMAIL / NO FILE CHANGE")
