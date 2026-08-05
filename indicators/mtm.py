import pandas as pd


def calculate_mtm(
    df: pd.DataFrame,
    period: int = 5,
) -> pd.Series:
    """
    Calculate Momentum (MTM).

    MTM measures the difference between the current
    closing price and the closing price a selected
    number of periods ago.

    Parameters
    ----------
    df : pandas.DataFrame
        OHLCV market data containing a Close column.
    period : int
        Lookback period. Default is 5.

    Returns
    -------
    pandas.Series
        Momentum values.
    """

    mtm = df["Close"] - df["Close"].shift(period)

    return mtm