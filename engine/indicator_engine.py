from indicators.dmi import calculate_dmi
from indicators.wr import calculate_wr
from indicators.psy import calculate_psy
from indicators.kdj import calculate_j
from indicators.mtm import calculate_mtm
from indicators.roc import calculate_roc


def build_indicators(df):
    """
    Build all technical indicators.

    Parameters
    ----------
    df : pandas.DataFrame
        OHLCV market data.

    Returns
    -------
    pandas.DataFrame
        Original dataframe with indicator columns added.
    """

    df["WR14"] = calculate_wr(df)
  
    df["PSY5"] = calculate_psy(df, period=5)

    df["KDJ"] = calculate_j(df)

    df["ROC5"] = calculate_roc(df, period=5)

    df["MTM5"] = calculate_mtm(df, period=5)

    dmi = calculate_dmi(df, period=13)

    df["PLUS_DI"] = dmi["PLUS_DI"]
    df["MINUS_DI"] = dmi["MINUS_DI"]
    df["ADX"] = dmi["ADX"]
    df["DMI_OSC"] = dmi["DMI_OSC"]

    return df
