
from app.news_collector import collect_news


def fetch_stock_news(ticker: str):
    """
    Fetch unique news articles for a stock ticker.
    """

    ticker = ticker.strip().upper()

    articles = collect_news(ticker)

    return articles