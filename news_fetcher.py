import requests


def fetch_news():

    news_text = ""

    # 🔥 Keywords
    keywords = [
        "stock", "market", "earnings", "profit",
        "ipo", "bank", "revenue", "growth"
    ]

    # -------------------------------
    # 🔥 SOURCE 1: NEWSAPI
    # -------------------------------
    try:
        url = "https://newsapi.org/v2/top-headlines"

        params = {
            "country": "in",
            "category": "business",
            "pageSize": 30,
            "apiKey": "86226ba8dcea4fdb8c61a7396f0453d9"
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        for article in data.get("articles", []):
            title = article.get("title", "")
            desc = article.get("description", "")

            if title:
                news_text += title + ". "
            if desc:
                news_text += desc + ". "

    except Exception as e:
        print("NewsAPI error:", e)

    # -------------------------------
    # 🔥 SOURCE 2: GNEWS
    # -------------------------------
    try:
        url = "https://gnews.io/api/v4/search"

        params = {
            "q": "stock market India",
            "lang": "en",
            "max": 20,
            "apikey": "1e8c2fbb6b05d2fee190b8ef15e83c62"
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        for article in data.get("articles", []):
            title = article.get("title", "")
            desc = article.get("description", "")

            if title:
                news_text += title + ". "
            if desc:
                news_text += desc + ". "

    except Exception as e:
        print("GNews error:", e)

    # -------------------------------
    # 🔥 CLEANING
    # -------------------------------
    sentences = list(set(news_text.split(".")))

    clean_sentences = [
        s.strip() for s in sentences
        if len(s.strip()) > 20
    ]

    # -------------------------------
    # 🔥 PRIORITIZATION
    # -------------------------------
    priority_keywords = [
        "profit", "earnings", "growth", "loss",
        "deal", "revenue", "ipo"
    ]

    scored = []

    for s in clean_sentences:
        score = sum(1 for k in priority_keywords if k in s.lower())
        scored.append((score, s))

    scored = sorted(scored, key=lambda x: x[0], reverse=True)

    top_sentences = [s for _, s in scored[:100]]

    clean_news = ". ".join(top_sentences)

    # 🔥 FALLBACK
    if len(clean_news) < 100:
        clean_news = (
            "Infosys reports strong earnings. "
            "ICICI Bank shows profit growth. "
            "Reliance expands its energy business. "
            "TCS signs new global deal."
        )

    return clean_news