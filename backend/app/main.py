from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from app.news import fetch_stock_news
from app.models.finbert import analyze_sentiment
from app.models.reyzer import analyze_reyzer
from app.models.vader import analyze_vader
from app.models.textblob_model import analyze_textblob

app = FastAPI(
    title="Sentock - Stock Sentiment Analysis",
    description="Stock news and sentiment analysis API",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    ticker: str



def validate_ticker(ticker: str) -> str | None:
    """
    Validate a ticker and return its Yahoo Finance symbol.
    Supports US, NSE, and BSE symbols.
    """

    ticker = ticker.strip().upper()

    # If the user provides an explicit exchange suffix,
    # validate that exact symbol.
    if ticker.endswith((".NS", ".BO")):
        candidates = [ticker]

    # Indian ticker entered without a suffix:
    # Try NSE first, then BSE.
    elif ticker.isalnum() or "." in ticker:
        candidates = [
            ticker + ".NS",
            ticker + ".BO",
            ticker
        ]

    else:
        return None

    for candidate in candidates:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + quote(candidate, safe="")
            + "?range=5d&interval=1d"
        )

        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        try:
            with urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))

            chart = data.get("chart", {})
            results = chart.get("result")

            if results:
                return candidate

        except HTTPError as error:
            if error.code in (400, 404):
                continue

            raise HTTPException(
                status_code=503,
                detail="Stock symbol validation service is temporarily unavailable."
            )

        except (URLError, TimeoutError):
            raise HTTPException(
                status_code=503,
                detail="Could not verify the stock symbol right now. Please try again."
            )

    return None

@app.post("/api/analyze")
def analyze_stock(request: AnalysisRequest):
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=400,
            detail="Ticker cannot be empty"
        )
    
    # Validate the ticker before collecting news
    try:
        validated_ticker = validate_ticker(ticker)
    except HTTPException:
        raise

    if not validated_ticker:
        raise HTTPException(
            status_code=400,
            detail=f"'{ticker}' is not a recognized stock ticker. Please enter a valid ticker symbol."
        )

    ticker = validated_ticker

    # 1. Collect news
    try:
        articles = fetch_stock_news(ticker)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"News collection failed: {str(error)}"
        )

    headlines = [article["title"] for article in articles]

    # 2. Run model suite
    try:
        finbert_results = analyze_sentiment(headlines, batch_size=8)
        reyzer_results = analyze_reyzer(headlines)
        vader_results = analyze_vader(headlines)
        textblob_results = analyze_textblob(headlines)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment analysis failed: {str(error)}"
        )

    # 3. Model weights
    weights = {
        "finbert": 0.40,
        "reyzer": 0.30,
        "vader": 0.15,
        "textblob": 0.15,
    }

    # 4. Article-level ensemble
    ensemble_scores = []
    for article, finbert, reyzer, vader, textblob in zip(
        articles, finbert_results, reyzer_results, vader_results, textblob_results
    ):
        ensemble_score = (
            weights["finbert"] * finbert["sentiment_score"]
            + weights["reyzer"] * reyzer["sentiment_score"]
            + weights["vader"] * vader["sentiment_score"]
            + weights["textblob"] * textblob["sentiment_score"]
        )

        if ensemble_score > 0.05:
            ensemble_sentiment = "positive"
        elif ensemble_score < -0.05:
            ensemble_sentiment = "negative"
        else:
            ensemble_sentiment = "neutral"

        article["finbert"] = finbert
        article["reyzer"] = reyzer
        article["vader"] = vader
        article["textblob"] = textblob
        article["ensemble_score"] = ensemble_score
        article["ensemble_sentiment"] = ensemble_sentiment

        ensemble_scores.append(ensemble_score)

    # 5. Model averages
    if articles:
        finbert_average_score = sum(r["sentiment_score"] for r in finbert_results) / len(articles)
        reyzer_average_score = sum(r["sentiment_score"] for r in reyzer_results) / len(articles)
        vader_average_score = sum(r["sentiment_score"] for r in vader_results) / len(articles)
        textblob_average_score = sum(r["sentiment_score"] for r in textblob_results) / len(articles)
        ensemble_average_score = sum(ensemble_scores) / len(articles)
    else:
        finbert_average_score = None
        reyzer_average_score = None
        vader_average_score = None
        textblob_average_score = None
        ensemble_average_score = None

    # 6. Overall ticker classification
    if ensemble_average_score is None:
        overall_sentiment = "no_news"
    elif ensemble_average_score > 0.05:
        overall_sentiment = "positive"
    elif ensemble_average_score < -0.05:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"

    return {
        "ticker": ticker,
        "articles_analyzed": len(articles),
        "articles": articles,
        "model_average_scores": {
            "finbert": finbert_average_score,
            "reyzer": reyzer_average_score,
            "vader": vader_average_score,
            "textblob": textblob_average_score,
        },
        "ensemble_weights": weights,
        "ensemble_score": ensemble_average_score,
        "overall_sentiment": overall_sentiment,
        "status": "All four sentiment models completed"
    }

# --------------------------------------------------
# Frontend Static Files & Page Routes
# --------------------------------------------------

# Path to the frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/analyze")
    def serve_analyze():
        return FileResponse(os.path.join(frontend_dir, "analyze.html"))