import yfinance as yf
import pandas as pd


# 🔥 BULK DOWNLOAD
def get_bulk_stock_data(tickers):
    try:
        df = yf.download(
            tickers,
            period="3mo",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False
        )
        return df
    except Exception as e:
        print("Bulk download error:", e)
        return None


# 🔥 PREFILTER (RELAXED)
def prefilter(df):
    if df is None or df.empty or len(df) < 20:
        return False

    df = df.copy()
    df["MA20"] = df["Close"].rolling(20).mean()

    latest = df.iloc[-1]

    try:
        close = float(latest["Close"])
        ma20 = float(latest["MA20"])
    except:
        return False

    return close > ma20 * 0.97


# 🔥 TECHNICAL SCORE
def technical_score(df):
    if len(df) < 50:
        return 0

    df = df.copy()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    latest = df.iloc[-1]

    try:
        close = float(latest["Close"])
        ma20 = float(latest["MA20"])
        ma50 = float(latest["MA50"])
    except:
        return 0

    score = 0

    # Trend
    if close > ma20:
        score += 0.5

    if ma20 > ma50:
        score += 0.5

    # Momentum
    returns = df["Close"].pct_change().dropna()

    if len(returns) > 0:
        momentum = float(returns.tail(10).mean())
        if momentum > 0:
            score += 0.5

    return min(score, 1)


# 🔥 FINAL SMART SCORING (KEY UPGRADE)
def analyze_stock_bulk(ticker, sentiment_score, bulk_data):

    try:
        df = bulk_data[ticker].dropna()
    except:
        return None

    if df is None or df.empty:
        return None

    # Prefilter
    if not prefilter(df):
        return None

    tech = technical_score(df)

    # 🔥 FIX 1 — Reduce weight if no sentiment
    if abs(sentiment_score) < 0.05:
        sentiment_weight = 0.2
    else:
        sentiment_weight = 0.7

    # 🔥 FIX 2 — Combine scores
    final_score = (sentiment_weight * sentiment_score) + (0.3 * tech)

    # 🔥 FIX 3 — Boost stocks mentioned in news
    if abs(sentiment_score) > 0.05:
        final_score += 0.1

    # 🔥 FIX 4 — Penalize random technical-only stocks
    if sentiment_score == 0 and tech < 0.7:
        return None

    return {
        "ticker": ticker,
        "sentiment": round(sentiment_score, 3),
        "technical": round(tech, 3),
        "final_score": round(final_score, 3)
    }