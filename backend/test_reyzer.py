
from app.models.reyzer import analyze_reyzer

headlines = [
    "Company reports record profits and strong revenue growth",
    "Shares plunge after disappointing earnings and weak guidance",
    "Company announces its quarterly financial results",
]

results = analyze_reyzer(headlines)

for headline, result in zip(headlines, results):
    print("\nHeadline:", headline)
    print("Result:", result)