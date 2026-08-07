import pandas as pd

from indicators.mtm import calculate_mtm


df = pd.DataFrame(
    {
        "Close": [
            100, 101, 102, 101, 103,
            103, 104, 102, 103, 105,
            106, 105, 107, 108, 110
        ]
    }
)

mtm3 = calculate_mtm(df, period=3)
mtm10 = calculate_mtm(df, period=10)

result = pd.DataFrame(
    {
        "Close": df["Close"],
        "MTM3": mtm3,
        "MTM10": mtm10,
    }
)

print(result)
