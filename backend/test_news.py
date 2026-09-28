
from app.news_collector import collect_news

ticker = "NVDA"

articles = collect_news(ticker)

print("Ticker:", ticker)
print("Total unique articles:", len(articles))

for i, article in enumerate(articles[:10], start=1):
    print(f"\nArticle {i}")
    print("Title:", article["title"])
    print("Source:", article["source"])
    print("Date:", article["published_at"])
    print("URL:", article["url"])