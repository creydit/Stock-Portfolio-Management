
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# --------------------------------------------------
# 1. Initialize VADER
# --------------------------------------------------

analyzer = SentimentIntensityAnalyzer()


# --------------------------------------------------
# 2. Analyze financial headlines
# --------------------------------------------------

def analyze_vader(headlines):

    if not headlines:
        return []

    results = []

    for headline in headlines:

        scores = analyzer.polarity_scores(headline)

        positive = float(scores["pos"])
        negative = float(scores["neg"])
        neutral = float(scores["neu"])

        # VADER's compound score is already normalized
        # between -1 and +1.
        sentiment_score = float(scores["compound"])

        sentiment = (
            "positive"
            if sentiment_score > 0.05
            else "negative"
            if sentiment_score < -0.05
            else "neutral"
        )

        results.append({
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        })

    return results