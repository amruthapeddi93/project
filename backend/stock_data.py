import yfinance as yf


def get_historical_stock_data(ticker: str, period: str):
    stock = yf.Ticker(ticker)

    data = stock.history(period=period, interval="1d", auto_adjust=False)

    if data.empty:
        return None

    # Convert the index into a Date column
    data = data.reset_index()

    # Select required historical stock columns
    data = data[["Date", "Open", "High", "Low", "Close", "Volume"]]

    # Remove missing values
    data = data.dropna()

    # Format date
    data["Date"] = data["Date"].dt.strftime("%Y-%m-%d")

    return data
