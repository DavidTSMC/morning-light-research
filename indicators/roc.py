import pandas as pd


def calculate_roc(
    df: pd.DataFrame,
    period: int = 5,
) -> pd.Series:
    """
    Calculate Rate of Change (ROC).

    ROC measures the percentage change between
    the current closing price and the closing
    price a selected number of periods ago.
    """

    previous_close = df["Close"].shift(period)

    roc = (
        (df["Close"] - previous_close)
        / previous_close
        * 100
    )

    return roc