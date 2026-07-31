from engine.download_engine import download_stock
from indicators.wr import calculate_wr

df = download_stock()

df["WR14"] = calculate_wr(df)

print(df[["Close", "WR14"]].tail())