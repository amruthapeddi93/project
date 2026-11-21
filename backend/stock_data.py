

import os
import requests
import pandas as pd
from datetime import datetime, timezone



ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def get_historical_stock_data(ticker: str, period: str):

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
       raise ValueError("Alpha Vantage API key is missing")

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "apikey": api_key    }

    response = requests.get(
        ALPHA_VANTAGE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    # Handle API errors
    if "Error Message" in result:
        raise ValueError(result["Error Message"])

    if "Note" in result:
        raise ValueError("Alpha Vantage API rate limit reached")

    if "Information" in result:
        raise ValueError(result["Information"])

    time_series = result.get("Time Series (Daily)")

    if not time_series:
        return None

    # Convert API response into DataFrame
    data = pd.DataFrame.from_dict(
        time_series,
        orient="index"
    )

    data = data.reset_index()

    data.columns = [
        "Date", "Open", "High", "Low", "Close", "Volume"
    ]

    # Convert numeric columns
    numeric_columns = [
        "Open", "High", "Low", "Close", "Volume"
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Remove missing records
    original_count = len(data)

    data = data.dropna(
        subset=["Date"] + numeric_columns
    )

    # Validate OHLC values
    data = data[
        (data["High"] >= data["Low"]) &
        (data["High"] >= data["Open"]) &
        (data["High"] >= data["Close"]) &
        (data["Low"] <= data["Open"]) &
        (data["Low"] <= data["Close"]) &
        (data["Volume"] >= 0)
    ].copy()

    if data.empty:
        return None

    # Sort oldest to newest
    data["Date"] = pd.to_datetime(data["Date"])

    data = data.sort_values(
        by="Date"
    ).reset_index(drop=True)

    removed_records = original_count - len(data)

    # Calculate SMA 20
    data["SMA_20"] = data["Close"].rolling(
        window=20
    ).mean()

    # Calculate EMA 12
    data["EMA_12"] = data["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    # Calculate RSI 14
    price_change = data["Close"].diff()

    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    avg_gain = gains.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    avg_loss = losses.ewm(
        alpha=1/14,
        min_periods=14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    data["RSI_14"] = 100 - (100 / (1 + rs))

    # Handle cases where prices only increase or remain unchanged
    data.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI_14"
    ] = 100

    data.loc[
        (avg_loss == 0) & (avg_gain == 0),
        "RSI_14"
    ] = 50

    # Calculate MACD
    ema_12 = data["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema_26 = data["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    data["MACD"] = ema_12 - ema_26

    data["MACD_Signal"] = data["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    data["MACD_Histogram"] = (
        data["MACD"] - data["MACD_Signal"]
    )

    # Period filtering
    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825
    }

    if period in period_days:
        start_date = (
            pd.Timestamp.now().normalize()
            - pd.Timedelta(days=period_days[period])
        )

        data = data[
            data["Date"] >= start_date
        ].copy()

    if data.empty:
        return None

    # Format dates
    data["Date"] = data["Date"].dt.strftime(
        "%Y-%m-%d"
    )

    # Latest indicator values
    latest = data.iloc[-1]

    indicators = {
        "SMA_20": latest["SMA_20"],
        "EMA_12": latest["EMA_12"],
        "RSI_14": latest["RSI_14"],
        "MACD": latest["MACD"],
        "MACD_Signal": latest["MACD_Signal"],
        "MACD_Histogram": latest["MACD_Histogram"],
        "Volume": latest["Volume"]
    }

    # Convert NaN values to None
    indicators = {
        key: None if pd.isna(value) else float(value)
        for key, value in indicators.items()
    }

    return {
        "ticker": ticker,
        "data": data,
        "total_records": len(data),
        "removed_records": removed_records,
        "indicators": indicators,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }
