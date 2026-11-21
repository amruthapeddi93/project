
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

if not api_key:
    print("API key not found!")
else:
    url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "IBM",
        "outputsize": "compact",
        "apikey": api_key
    }

    response = requests.get(url, params=params, timeout=30)

    result = response.json()

    if "Time Series (Daily)" in result:
        print("SUCCESS: Alpha Vantage API is working!")
        print("Records received:", len(result["Time Series (Daily)"]))

    elif "Error Message" in result:
        print("API ERROR:", result["Error Message"])

    elif "Note" in result:
        print("API LIMIT:", result["Note"])

    elif "Information" in result:
        print("API INFORMATION:", result["Information"])

    else:
        print("Unexpected response:", result)
