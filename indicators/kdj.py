import pandas as pd


def calculate_j(
    df: pd.DataFrame,
    period: int = 9,
    k_smooth: int = 3,
    d_smooth: int = 3,
) -> pd.Series:
    low_n = df["Low"].rolling(window=period, min_periods=period).min()
    high_n = df["High"].rolling(window=period, min_periods=period).max()

    denominator = (high_n - low_n).replace(0, pd.NA)
    rsv = (df["Close"] - low_n) / denominator * 100

    k = rsv.ewm(alpha=1 / k_smooth, adjust=False).mean()
    d = k.ewm(alpha=1 / d_smooth, adjust=False).mean()
    j = 3 * k - 2 * d

    return j