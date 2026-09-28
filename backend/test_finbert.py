
from app.models.finbert import analyze_sentiment

headlines = [
    "NVIDIA reports record revenue and strong earnings growth",
    "NVIDIA shares fall after disappointing quarterly results",
    "NVIDIA announces a new product at its annual conference"
]

results = analyze_sentiment(headlines)

for headline, result in zip(headlines, results):
    print("\nHeadline:", headline)
    print(result)