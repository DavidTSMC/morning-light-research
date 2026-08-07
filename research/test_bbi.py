import pandas as pd

from indicators.bbi import calculate_bbi

close = pd.Series(range(1, 31), dtype=float)

result = calculate_bbi(close)

print(result.tail(5))