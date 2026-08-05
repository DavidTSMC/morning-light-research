import numpy as np
import pandas as pd


def calculate_dmi(
    df: pd.DataFrame,
    period: int = 13,
) -> pd.DataFrame:
    """
    Calculate +DI, -DI, ADX and DMI Oscillator.

    period=13 matches the current chart setting.
    """

   
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    close = df["Close"].squeeze()

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
    np.where(
        (up_move > down_move) & (up_move > 0),
        up_move,
        0.0,
    ).ravel(),
    index=df.index,
)

    minus_dm = pd.Series(
    np.where(
        (down_move > up_move) & (down_move > 0),
        down_move,
        0.0,
    ).ravel(),
    index=df.index,
)
    

    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    plus_dm_smoothed = plus_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    minus_dm_smoothed = minus_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    plus_di = 100 * plus_dm_smoothed / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm_smoothed / atr.replace(0, np.nan)

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum

    adx = dx.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return pd.DataFrame(
        {
            "PLUS_DI": plus_di,
            "MINUS_DI": minus_di,
            "ADX": adx,
            "DMI_OSC": plus_di - minus_di,
        },
        index=df.index,
    )