
from app.models.vader import analyze_vader
from app.models.textblob_model import analyze_textblob


headlines = [
    "Company reports record profits and strong revenue growth",
    "Shares plunge after disappointing earnings and weak guidance",
    "Company announces its quarterly financial results",
]

vader_results = analyze_vader(headlines)
textblob_results = analyze_textblob(headlines)

for i, headline in enumerate(headlines):

    print("\nHeadline:", headline)

    print("VADER:")
    print(vader_results[i])

    print("TextBlob:")
    print(textblob_results[i])