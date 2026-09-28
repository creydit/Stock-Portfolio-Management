
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime, timezone


def get_google_news(ticker):
    """
    Fetch news headlines from Google News RSS.
    Returns a list of article dictionaries.
    """

    query = quote(f'"{ticker}" stock news')

    url = (
        "https://news.google.com/rss/search"
        f"?q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    root = ET.fromstring(response.content)

    articles = []

    for item in root.findall(".//item"):
        title = item.findtext("title")
        link = item.findtext("link")
        pub_date = item.findtext("pubDate")
        source_element = item.find("source")

        source = (
            source_element.text
            if source_element is not None
            else None
        )

        if not title:
            continue

        articles.append({
            "ticker": ticker,
            "title": title.strip(),
            "source": source,
            "published_at": pub_date,
            "url": link,
            "provider": "Google News"
        })

    return articles


def get_finviz_news(ticker):
    """
    Fetch news from the Finviz quote page.
    Returns a list of article dictionaries.
    """

    url = f"https://finviz.com/quote.ashx?t={ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    articles = []

    table = soup.find("table", id="news-table")

    if table is None:
        return articles

    for row in table.find_all("tr"):
        link_tag = row.find("a")

        if link_tag is None:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")

        time_cell = row.find("td")

        published_at = (
            time_cell.get_text(" ", strip=True)
            if time_cell
            else None
        )

        if not title:
            continue

        articles.append({
            "ticker": ticker,
            "title": title,
            "source": None,
            "published_at": published_at,
            "url": link,
            "provider": "Finviz"
        })

    return articles


def collect_news(ticker):
    """
    Combine news from Google News and Finviz,
    then remove duplicate headlines.
    """

    ticker = ticker.strip().upper()

    articles = []

    # Collect from each source independently.
    for collector in (
        get_google_news,
        get_finviz_news
    ):
        try:
            results = collector(ticker)
            articles.extend(results)

        except requests.RequestException as error:
            print(
                f"{collector.__name__} failed: {error}"
            )

        except Exception as error:
            print(
                f"Unexpected error in "
                f"{collector.__name__}: {error}"
            )

    # Deduplicate headlines.
    unique_articles = []
    seen_titles = set()

    for article in articles:
        normalized_title = (
            article["title"]
            .lower()
            .strip()
        )

        if normalized_title in seen_titles:
            continue

        seen_titles.add(normalized_title)
        unique_articles.append(article)

    return unique_articles