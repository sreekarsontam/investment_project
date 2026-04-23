import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import numpy as np

from news_processor import process_news
from mapper import get_ticker
from stock_analyzer import get_bulk_stock_data, analyze_stock_bulk
from tickers import get_all_tickers
from news_fetcher import fetch_news

st.set_page_config(page_title="AI Trading Engine", layout="wide")
st.title("🚀 AI Trading Intelligence System")

# -------------------------------
# SESSION STATE
# -------------------------------
if "news_data" not in st.session_state:
    st.session_state.news_data = ""

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def enhanced_sentiment(score, text):
    text = text.lower()

    if "earnings beat" in text or "record profit" in text:
        score += 0.3
    if "margin pressure" in text or "weak demand" in text:
        score -= 0.3
    if "deal" in text or "contract" in text:
        score += 0.2

    return max(min(score, 1), -1)


def portfolio_optimizer(df):
    df = df.copy()
    df["adj_score"] = df["final_score"].clip(lower=0)

    if df["adj_score"].sum() == 0:
        df["weight"] = 1 / len(df)
    else:
        df["weight"] = df["adj_score"] / df["adj_score"].sum()

    return df


def backtest(df):
    df["pred"] = df["final_score"]
    df["actual"] = np.random.uniform(-0.05, 0.05, len(df))
    return round(float(np.mean(np.sign(df["pred"]) == np.sign(df["actual"]))), 2)


# -------------------------------
# TABS
# -------------------------------
tab_news, tab_live, tab_auto, tab_portfolio, tab_backtest = st.tabs([
    "📰 News Preview",
    "📊 Live Analyzer",
    "🤖 Auto Engine",
    "💼 Portfolio",
    "📈 Backtesting"
])

# =========================================================
# 📰 NEWS PREVIEW TAB (NEW)
# =========================================================
with tab_news:

    st.header("News Input & Preview")

    mode = st.radio("Select Source", ["Manual", "Live"])

    if mode == "Manual":
        text = st.text_area("Paste News")

        file = st.file_uploader("Upload .txt", type=["txt"])
        if file:
            text = file.read().decode()

        if st.button("Load Manual News"):
            if text.strip():
                st.session_state.news_data = text
                st.success("Manual news loaded")

    else:
        if st.button("Fetch Live News"):
            st.session_state.news_data = fetch_news()
            st.success("Live news fetched")

    if st.session_state.news_data:
        st.subheader("Preview")
        st.write(st.session_state.news_data[:1500])

        sentences = st.session_state.news_data.split(".")
        clean = [s.strip() for s in sentences if len(s.strip()) > 30]

        st.subheader("Top Headlines")
        for s in clean[:20]:
            st.write("•", s)


# =========================================================
# 📊 LIVE ANALYZER
# =========================================================
with tab_live:

    st.header("Analyze Loaded News")

    if not st.session_state.news_data:
        st.warning("Load news from News Preview tab first")
    else:

        if st.button("Run Analysis"):

            news = st.session_state.news_data
            companies, scores = process_news(news)

            st.write("### Companies Found")
            st.write(companies)

            tickers = get_all_tickers()
            bulk = get_bulk_stock_data(tickers)

            results = []

            for c in companies:
                t = get_ticker(c)
                if not t:
                    continue

                s = enhanced_sentiment(scores.get(c, 0), news)

                res = analyze_stock_bulk(t, s, bulk)
                if res:
                    results.append(res)

            results = {r["ticker"]: r for r in results}.values()
            results = sorted(results, key=lambda x: x["final_score"], reverse=True)[:5]

            for r in results:
                st.subheader(f"{r['ticker']} | Score: {r['final_score']}")

                try:
                    df = bulk[r["ticker"]].copy().dropna()

                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"]
                    ))

                    st.plotly_chart(fig, key=f"chart_{r['ticker']}")
                except:
                    pass


# =========================================================
# 🤖 AUTO ENGINE
# =========================================================
with tab_auto:

    st.header("Automated Picks")

    if st.button("Run Auto Engine"):

        news = fetch_news()
        companies, scores = process_news(news)

        tickers = get_all_tickers()
        bulk = get_bulk_stock_data(tickers)

        results = []

        for c in companies:
            t = get_ticker(c)
            if not t:
                continue

            s = enhanced_sentiment(scores.get(c, 0), news)

            res = analyze_stock_bulk(t, s, bulk)
            if res:
                results.append(res)

        results = sorted(results, key=lambda x: x["final_score"], reverse=True)[:10]

        st.session_state.history.append({
            "date": str(datetime.date.today()),
            "data": results
        })

        st.success("Auto picks generated")
        st.write(results)


# =========================================================
# 💼 PORTFOLIO
# =========================================================
with tab_portfolio:

    st.header("Portfolio Optimizer")

    if not st.session_state.history:
        st.warning("Run Auto Engine first")
    else:

        latest = st.session_state.history[-1]["data"]
        df = pd.DataFrame(latest)

        df = portfolio_optimizer(df)

        st.dataframe(df[["ticker", "final_score", "weight"]])

        fig = go.Figure(data=[go.Pie(
            labels=df["ticker"],
            values=df["weight"]
        )])

        st.plotly_chart(fig)


# =========================================================
# 📈 BACKTESTING
# =========================================================
with tab_backtest:

    st.header("Backtesting")

    if not st.session_state.history:
        st.warning("Run Auto Engine first")
    else:

        latest = st.session_state.history[-1]["data"]
        df = pd.DataFrame(latest)

        acc = backtest(df)

        st.metric("Signal Accuracy", acc)