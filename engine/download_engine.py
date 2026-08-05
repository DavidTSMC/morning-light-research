import yfinance as yf
from pathlib import Path




def download_stock(symbol="2330.TW", period="1y"):
    print(f"Downloading {symbol} ...")

    df = yf.download(
        symbol,
        period=period,
        auto_adjust=False,
        progress=False
    )

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = output_dir / f"{symbol.replace('.', '_')}.csv"

    df.to_csv(filename)

    print(f"Saved to: {filename}")

    return df


if __name__ == "__main__":
    download_stock()