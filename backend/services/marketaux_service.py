import os
import logging

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"


async def fetch_stock_news(
    symbol: str,
    country: str,
    limit: int = 10,
):
    api_token = os.getenv("MARKETAUX_API_TOKEN")

    if not api_token:
        raise ValueError("MARKETAUX_API_TOKEN is missing from the environment.")

    symbol = symbol.strip().upper()
    country = country.strip().lower()

    base_params = {
        "api_token": api_token,
        "symbols": symbol,
        "filter_entities": "true",
        "must_have_entities": "true",
        "language": "en",
        "limit": max(1, min(limit, 50)),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        # First request: exact symbol and exchange country
        params = {
            **base_params,
            "countries": country,
        }

        response = await client.get(
            MARKETAUX_URL,
            params=params,
        )

        if response.status_code != 200:
            logger.error("Marketaux error: %s", response.text)
            raise RuntimeError(f"Marketaux API error ({response.status_code})")

        result = response.json()
        articles = result.get("data") or []

        logger.info(
            "Marketaux search for %s in %s returned %s articles",
            symbol,
            country,
            len(articles),
        )

        # Second request: retry without exchange-country filtering
        if not articles:
            logger.info("Retrying Marketaux search without country filter.")

            response = await client.get(
                MARKETAUX_URL,
                params=base_params,
            )

            if response.status_code != 200:
                logger.error("Marketaux fallback error: %s", response.text)
                raise RuntimeError(f"Marketaux fallback error ({response.status_code})")

            result = response.json()
            articles = result.get("data") or []

            logger.info(
                "Fallback search for %s returned %s articles",
                symbol,
                len(articles),
            )

        return articles
