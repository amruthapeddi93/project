import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

url = "https://www.alphavantage.co/query"

params = {
    "function": "OVERVIEW",
    "symbol": "INFY.BSE",
    "apikey": API_KEY
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print(response.json())