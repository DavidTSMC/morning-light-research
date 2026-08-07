"""
Morning Light Research
OBV — On-Balance Volume

Research parameters:
    OBV
    MA3
    MA10

Principle:
    Evidence first.
    Descriptive evidence only.
    No trading decisions.
"""

import pandas as pd


def calculate_obv(
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).

    close > previous close  -> + volume
    close < previous close  -> - volume
    close = previous close  -> no change
    """

    direction = close.diff()

    signed_volume = pd.Series(
        0.0,
        index=close.index,
        dtype=float,
    )

    signed_volume[direction > 0] = volume[direction > 0]
    signed_volume[direction < 0] = -volume[direction < 0]

    obv = signed_volume.cumsum()

    return obv.rename("OBV")


def calculate_obv_with_ma(
    close: pd.Series,
    volume: pd.Series,
) -> pd.DataFrame:
    """
    Return:
        OBV
        OBV_MA3
        OBV_MA10
    """

    obv = calculate_obv(close, volume)

    result = pd.DataFrame(
        {
            "OBV": obv,
            "OBV_MA3": obv.rolling(window=3).mean(),
            "OBV_MA10": obv.rolling(window=10).mean(),
        }
    )

    return result