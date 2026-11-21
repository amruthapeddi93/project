
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

BASE_URL = "https://www.alphavantage.co/query"


def search_company(keyword):

    if not keyword or not keyword.strip():
        return {
            "success": False,
            "message": "Please enter a company name or ticker symbol.",
            "results": []
        }

    if not API_KEY:
        raise ValueError("Alpha Vantage API key is missing.")

    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keyword.strip(),
        "apikey": API_KEY
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    # Handle API errors and rate limits
    if "Error Message" in data:
        raise ValueError(data["Error Message"])

    if "Note" in data or "Information" in data:
        raise RuntimeError(
            data.get("Note") or data.get("Information")
        )

    matches = data.get("bestMatches", [])

    results = []

    for company in matches:

        results.append({
            "symbol": company.get("1. symbol"),
            "name": company.get("2. name"),
            "type": company.get("3. type"),
            "region": company.get("4. region"),
            "currency": company.get("8. currency"),
            "match_score": company.get("9. matchScore")
        })

    return {
        "success": True,
        "query": keyword,
        "total_results": len(results),
        "results": results
    }
