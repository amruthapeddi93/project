from datetime import UTC, date, datetime
from typing import Annotated, Literal

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, FastAPI, HTTPException, Query

router = APIRouter(
    prefix="/company",
    tags=["Company Information & Financial Statements"],
)


def clean_value(value):
    """Convert Pandas and NumPy values into JSON-compatible values."""
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, (float, np.floating)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    return value


def get_company_profile(ticker: str):
    """Retrieve company profile information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or not (info.get("longName") or info.get("shortName")):
            return {
                "success": False,
                "message": "Company profile information is unavailable.",
                "data": None,
            }

        profile = {
            "symbol": info.get("symbol"),
            "company_name": info.get("longName") or info.get("shortName"),
            "short_name": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "business_summary": info.get("longBusinessSummary"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency"),
            "employees": clean_value(info.get("fullTimeEmployees")),
            "market_cap": clean_value(info.get("marketCap")),
            "current_price": clean_value(info.get("currentPrice")),
            "52_week_high": clean_value(info.get("fiftyTwoWeekHigh")),
            "52_week_low": clean_value(info.get("fiftyTwoWeekLow")),
            "dividend_yield": clean_value(info.get("dividendYield")),
            "pe_ratio": clean_value(info.get("trailingPE")),
            "eps": clean_value(info.get("trailingEps")),
        }

        return {
            "success": True,
            "message": "Company profile retrieved successfully.",
            "data": profile,
        }

    except Exception as e:  # noqa: BLE001
        return {
            "success": False,
            "message": f"Unable to retrieve company profile: {e!s}",
            "data": None,
        }


def get_financial_statement(stock, statement_type: str, frequency: str = "yearly"):
    """Retrieve income statement, balance sheet, or cash flow statement."""
    try:
        if statement_type == "income_statement":
            statement = (
                stock.income_stmt
                if frequency == "yearly"
                else stock.quarterly_income_stmt
            )
        elif statement_type == "balance_sheet":
            statement = (
                stock.balance_sheet
                if frequency == "yearly"
                else stock.quarterly_balance_sheet
            )
        elif statement_type == "cash_flow":
            statement = (
                stock.cashflow if frequency == "yearly" else stock.quarterly_cashflow
            )
        else:
            return {
                "success": False,
                "message": "Invalid financial statement type.",
                "data": None,
            }

        if statement is None or statement.empty:
            return {
                "success": False,
                "message": f"{statement_type.replace('_', ' ').title()} is unavailable.",
                "data": None,
            }

        records = []
        for metric in statement.index:
            values = {}
            for period in statement.columns:
                period_name = (
                    str(period.date()) if hasattr(period, "date") else str(period)
                )
                values[period_name] = clean_value(statement.loc[metric, period])

            records.append(
                {
                    "metric": str(metric),
                    "values": values,
                }
            )

        return {
            "success": True,
            "message": f"{statement_type.replace('_', ' ').title()} retrieved successfully.",
            "total_metrics": len(records),
            "data": records,
        }

    except Exception as e:  # noqa: BLE001
        return {
            "success": False,
            "message": f"Unable to retrieve {statement_type}: {e!s}",
            "data": None,
        }


def get_company_financial_information(ticker: str, frequency: str = "yearly"):
    """Retrieve company profile and financial statements."""
    try:
        stock = yf.Ticker(ticker)

        profile = get_company_profile(ticker)
        income_statement = get_financial_statement(stock, "income_statement", frequency)
        balance_sheet = get_financial_statement(stock, "balance_sheet", frequency)
        cash_flow = get_financial_statement(stock, "cash_flow", frequency)

        return {
            "success": True,
            "ticker": ticker.upper(),
            "frequency": frequency,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "company_profile": profile,
            "financial_statements": {
                "income_statement": income_statement,
                "balance_sheet": balance_sheet,
                "cash_flow_statement": cash_flow,
            },
        }

    except Exception as e:  # noqa: BLE001
        return {
            "success": False,
            "ticker": ticker.upper(),
            "message": f"Unable to retrieve company financial information: {e!s}",
            "data": None,
        }


@router.get("/{ticker}")
def company_financial_endpoint(
    ticker: str,
    frequency: Annotated[
        Literal["yearly", "quarterly"],
        Query(description="Reporting period frequency: 'yearly' or 'quarterly'"),
    ] = "yearly",
):
    """HTTP endpoint serving get_company_financial_information to historicalData.jsx."""
    symbol = ticker.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty.")

    result = get_company_financial_information(symbol, frequency)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("message"))

    return result


standalone_app = FastAPI(title="Module 2: Company Info & Financial Statements")
standalone_app.include_router(router)
