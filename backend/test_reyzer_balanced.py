from pathlib import Path
import joblib

# Locate saved balanced model
BACKEND_DIR = Path(__file__).resolve().parent
MODEL_DIR = BACKEND_DIR / "saved_models"

model = joblib.load(
    MODEL_DIR / "reyzer_balanced_model.joblib"
)

vectorizer = joblib.load(
    MODEL_DIR / "reyzer_balanced_vectorizer.joblib"
)

headlines = [
    "Company reports record profits and strong revenue growth",
    "Shares plunge after disappointing earnings and weak guidance",
    "Company announces its quarterly financial results",
]

# Convert headlines into TF-IDF features
X = vectorizer.transform(headlines)

# Get probabilities for each sentiment class
probabilities = model.predict_proba(X)

class_indices = {
    label: index
    for index, label in enumerate(model.classes_)
}

for headline, row in zip(headlines, probabilities):

    negative = row[class_indices["negative"]]
    neutral = row[class_indices["neutral"]]
    positive = row[class_indices["positive"]]

    score = positive - negative

    predicted = max(
        [
            ("positive", positive),
            ("negative", negative),
            ("neutral", neutral),
        ],
        key=lambda item: item[1]
    )[0]

    print("\nHeadline:", headline)
    print("Predicted sentiment:", predicted)
    print("Positive:", round(positive, 4))
    print("Negative:", round(negative, 4))
    print("Neutral:", round(neutral, 4))
    print("Sentiment score:", round(score, 4))