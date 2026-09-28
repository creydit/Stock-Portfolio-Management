
from textblob import TextBlob


# --------------------------------------------------
# 1. Analyze financial headlines
# --------------------------------------------------

def analyze_textblob(headlines):

    if not headlines:
        return []

    results = []

    for headline in headlines:

        blob = TextBlob(headline)

        # TextBlob polarity ranges from -1 to +1.
        polarity = float(blob.sentiment.polarity)

        # TextBlob subjectivity ranges from 0 to 1.
        subjectivity = float(blob.sentiment.subjectivity)

        sentiment = (
            "positive"
            if polarity > 0
            else "negative"
            if polarity < 0
            else "neutral"
        )

        # Convert polarity into positive/negative components.
        positive = max(polarity, 0.0)
        negative = max(-polarity, 0.0)

        # Remaining magnitude is assigned to neutral.
        neutral = 1.0 - abs(polarity)

        results.append({
            "sentiment": sentiment,
            "sentiment_score": polarity,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "subjectivity": subjectivity,
        })

    return results