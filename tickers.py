import pandas as pd

def get_all_tickers():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        tickers = df["Symbol"].apply(lambda x: x + ".NS").tolist()
        return tickers
    except Exception as e:
        print("Error loading tickers:", e)
        return []