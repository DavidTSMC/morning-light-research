import pandas as pd

from indicators.obv import calculate_obv_with_ma


close = pd.Series(
    [100, 101, 102, 101, 103, 103, 104, 102, 103, 105, 106, 105],
    dtype=float,
)

volume = pd.Series(
    [100, 120, 130, 140, 160, 110, 180, 200, 150, 220, 240, 210],
    dtype=float,
)

result = calculate_obv_with_ma(close, volume)

print(result)