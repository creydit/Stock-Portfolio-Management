
from pathlib import Path

import joblib


# --------------------------------------------------
# 1. Load the main binary ReyZer model
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BACKEND_DIR / "saved_models"

MODEL_PATH = MODEL_DIR / "reyzer_model.joblib"
VECTORIZER_PATH = MODEL_DIR / "reyzer_vectorizer.joblib"

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


# --------------------------------------------------
# 2. Analyze financial headlines
# --------------------------------------------------

def analyze_reyzer(headlines):

    if not headlines:
        return []

    X = vectorizer.transform(headlines)

    probabilities = model.predict_proba(X)

    class_indices = {
        label: index
        for index, label in enumerate(model.classes_)
    }

    results = []

    for row in probabilities:

        negative = float(
            row[class_indices["negative"]]
        )

        positive = float(
            row[class_indices["positive"]]
        )

        # Binary model has no neutral class.
        # This is a placeholder, not a neutral prediction.
        neutral = 1.0 - abs(positive - negative)

        sentiment_score = positive - negative

        sentiment = (
            "positive"
            if positive >= negative
            else "negative"
        )

        results.append({
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        })

    return results