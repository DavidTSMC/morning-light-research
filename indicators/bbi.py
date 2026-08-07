"""
Morning Light Research
BBI — Bull and Bear Index

Research parameters:
    MA3, MA5, MA10, MA24

Principle:
    Evidence first.
    Descriptive evidence only.
    No trading decisions.
"""

import pandas as pd


BBI_PERIODS = (3, 5, 10, 24)


def calculate_bbi(close: pd.Series, periods=BBI_PERIODS) -> pd.Series:
    """
    Calculate BBI as the arithmetic mean of
    moving averages for the selected periods.

    Default:
        BBI = (MA3 + MA5 + MA10 + MA24) / 4
    """
    moving_averages = [
        close.rolling(window=period).mean()
        for period in periods
    ]

    bbi = sum(moving_averages) / len(moving_averages)
    return bbi.rename("BBI")