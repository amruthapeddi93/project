import logging
import re

from fastapi import APIRouter, HTTPException, Query

from services.gemini_service import analyze_news
from services.marketaux_service import fetch_stock_news

router = APIRouter(
    prefix="/api/news",
    tags=["News Agent"],
)

logger = logging.getLogger(__name__)

MARKET_COUNTRIES = {
    "india": "in",
    "us": "us",
}


@router.get("/{symbol}")
async def get_stock_news(
    symbol: str,
    market: str = Query(
        ...,
        description="Supported markets: india or us",
    ),
):
    symbol = symbol.strip().upper()
    market = market.strip().lower()

    # Validate symbol.
    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol cannot be empty.",
        )

    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,19}", symbol):
        raise HTTPException(
            status_code=400,
            detail="Invalid stock symbol.",
        )

    # Validate market.
    country = MARKET_COUNTRIES.get(market)

    if not country:
        raise HTTPException(
            status_code=400,
            detail="Market must be india or us.",
        )

    # STEP 1: Fetch news independently.
    try:
        articles = await fetch_stock_news(
            symbol=symbol,
            country=country,
            limit=10,
        )

        articles = articles or []

        if not isinstance(articles, list):
            raise TypeError("News provider returned an invalid response.")

    except Exception:
        logger.exception(
            "News fetching failed for %s in %s",
            symbol,
            market,
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to fetch stock news from the news provider.",
        ) from None

    # STEP 2: Return a valid response if no news exists.
    if not articles:
        return {
            "success": True,
            "symbol": symbol,
            "market": market,
            "article_count": 0,
            "articles": [],
            "ai_analysis": None,
            "ai_analysis_status": "not_available",
            "message": "No news articles found for this stock.",
        }

    # STEP 3: Analyze news independently using Gemini.
    try:
        analysis = await analyze_news(
            symbol=symbol,
            articles=articles,
        )

        ai_status = "completed"
        ai_message = "News and sentiment analysis completed."

    except Exception:
        logger.exception(
            "AI analysis failed for %s",
            symbol,
        )

        analysis = None
        ai_status = "unavailable"
        ai_message = (
            "News was retrieved successfully, "
            "but AI sentiment analysis is temporarily unavailable."
        )

    # STEP 4: Always return fetched articles.
    return {
        "success": True,
        "symbol": symbol,
        "market": market,
        "article_count": len(articles),
        "articles": articles,
        "ai_analysis": analysis,
        "ai_analysis_status": ai_status,
        "message": ai_message,
    }
