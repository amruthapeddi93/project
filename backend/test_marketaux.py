import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("MARKETAUX_API_TOKEN")


def test_news(symbol, country):
    url = "https://api.marketaux.com/v1/news/all"

    params = {
        "api_token": API_TOKEN,
        "symbols": symbol,
        "countries": country,
        "filter_entities": "true",
        "language": "en",
        "limit": 5,
        "group_similar": "true",
    }

    response = requests.get(url, params=params, timeout=20)
    print("HTTP status:", response.status_code)
    response.raise_for_status()

    result = response.json()

    print(f"\nNews for {symbol} ({country})")
    print("Articles returned:", len(result.get("data", [])))

    for article in result.get("data", []):
        print("\nTitle:", article.get("title"))
        print("Published:", article.get("published_at"))
        print("Source:", article.get("source"))
        print("URL:", article.get("url"))

        for entity in article.get("entities", []):
            print(
                "Entity:",
                entity.get("symbol"),
                "| Sentiment:",
                entity.get("sentiment_score"),
            )


if __name__ == "__main__":
    if not API_TOKEN:
        raise ValueError("MARKETAUX_API_TOKEN is missing in .env")

    test_news("INFY", "in")
    test_news("AAPL", "us")
