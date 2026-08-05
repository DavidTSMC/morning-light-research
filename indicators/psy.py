import pandas as pd


def calculate_psy(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    Calculate Psychological Line (PSY).

    PSY measures the percentage of rising days
    during the selected rolling period.

    Parameters
    ----------
    df : pandas.DataFrame
        OHLCV market data containing a Close column.
    period : int
        Rolling lookback period. Default is 5.

    Returns
    -------
    pandas.Series
        PSY values scaled from 0 to 100.
    """

    rising_day = (df["Close"].diff() > 0).astype(int)

    psy = (
        rising_day
        .rolling(window=period, min_periods=period)
        .sum()

        / period
        * 100
    )

    return psy