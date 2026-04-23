import spacy
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from mapper import get_ticker   # 🔥 IMPORTANT

# 🔥 Load models
nlp = spacy.load("en_core_web_sm")

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")


# 🔥 COMPANY DICTIONARY
COMPANY_MAP = {
    "reliance": "Reliance Industries",
    "tcs": "Tata Consultancy Services",
    "infosys": "Infosys",
    "hdfc": "HDFC Bank",
    "icici": "ICICI Bank",
    "sbi": "State Bank of India",
    "axis": "Axis Bank",
    "kotak": "Kotak Mahindra Bank",
    "adani": "Adani Enterprises",
    "tata motors": "Tata Motors",
    "maruti": "Maruti Suzuki",
    "wipro": "Wipro",
    "lt": "Larsen & Toubro",
    "airtel": "Bharti Airtel"
}


# 🔥 STRICT FILTER WORDS
IGNORE_PATTERNS = [
    "forecast", "news", "update", "market", "ipo", "sector",
    "india", "department", "report", "analysis", "growth",
    "demand", "industry", "data", "system"
]


# 🔥 FINAL CLEAN COMPANY EXTRACTION
def extract_companies(text):

    found = set()
    text_lower = text.lower()

    # 🔥 1. DICTIONARY MATCH (STRONGEST)
    for key in COMPANY_MAP:
        if key in text_lower:
            found.add(COMPANY_MAP[key])

    # 🔥 2. SPACY (CONTROLLED)
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "ORG":

            name = ent.text.strip()

            # ❌ remove short / weak
            if len(name) < 3:
                continue

            # ❌ remove junk patterns
            if any(p in name.lower() for p in IGNORE_PATTERNS):
                continue

            # 🔥 ONLY KEEP IF EXISTS IN YOUR STOCK MAPPER
            ticker = get_ticker(name)

            if ticker:
                found.add(name)

    return list(found)


# 🔥 SENTIMENT
def get_sentiment(sentence):

    sentence = sentence[:300]

    inputs = tokenizer(sentence, return_tensors="pt", truncation=True)
    outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=1).detach().numpy()[0]

    negative, neutral, positive = probs
    score = float(positive - negative)

    # 🔥 Keyword boost
    s = sentence.lower()

    if any(w in s for w in ["growth", "profit", "strong", "deal", "expansion"]):
        score += 0.2

    if any(w in s for w in ["loss", "decline", "pressure", "weak"]):
        score -= 0.2

    score = max(min(score, 1), -1)

    if score > 0.05:
        sentiment = "positive"
    elif score < -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, score


# 🔥 FINAL PROCESS
def process_news(text):

    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]

    company_scores = {}

    for sentence in sentences:

        companies = extract_companies(sentence)

        if not companies:
            continue

        sentiment, score = get_sentiment(sentence)

        for company in companies:
            company_scores.setdefault(company, []).append(score)

    final_scores = {
        c: float(sum(scores) / len(scores)) if scores else 0
        for c, scores in company_scores.items()
    }

    return list(final_scores.keys()), final_scores