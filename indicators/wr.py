import pandas as pd


def calculate_wr(df, period=14):
    """
    Calculate Williams %R
    """

    highest_high = df["High"].rolling(period).max()
    lowest_low = df["Low"].rolling(period).min()

    wr = -100 * (highest_high - df["Close"]) / (highest_high - lowest_low)

    return wr