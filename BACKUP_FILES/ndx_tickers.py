import requests
import pandas as pd

def get_ndx_tickers():
    """
    Fetches the full Nasdaq‑100 (NDX) components list directly from Nasdaq.
    Returns a pandas DataFrame with tickers and company names.
    """

    url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    # Extract table data
    rows = data["data"]["data"]["rows"]

    # Convert to DataFrame
    df = pd.DataFrame(rows)
    df = df[["symbol", "companyName"]]

    return df


# Example usage:
if __name__ == "__main__":
    ndx_df = get_ndx_tickers()
    print(ndx_df)
    print(f"\nTotal tickers: {len(ndx_df)}")