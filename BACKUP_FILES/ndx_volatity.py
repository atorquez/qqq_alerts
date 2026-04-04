import requests
import pandas as pd
import yfinance as yf
from io import StringIO

import requests

def get_ndx_tickers():
    """
    Fetch Nasdaq-100 tickers from the official NASDAQ JSON API.
    This endpoint is stable and returns consistent structure.
    """
    url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    data = response.json()

    rows = data["data"]["data"]["rows"]
    tickers = [row["symbol"] for row in rows]

    return tickers


def get_last_day_variance(tickers):
    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="2d", interval="1d", progress=False)

            if df is None or len(df) < 2:
                continue

            prev_close = df["Close"].iloc[-2]
            last_close = df["Close"].iloc[-1]

            if pd.isna(prev_close) or pd.isna(last_close):
                continue

            pct_change = (last_close - prev_close) / prev_close * 100

            results.append({
                "Ticker": t,
                "Prev_Close": float(prev_close),
                "Last_Close": float(last_close),
                "Pct_Change": float(pct_change)
            })

        except Exception:
            continue

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df

    return results_df.sort_values("Pct_Change", ascending=False)


if __name__ == "__main__":
    tickers = get_ndx_tickers()
    print(f"Loaded {len(tickers)} NDX tickers")

    vol_df = get_last_day_variance(tickers)
    print(vol_df.head(10))
    print(vol_df.tail(10))