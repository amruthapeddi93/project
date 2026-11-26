import logging
import os
import re

import numpy as np
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# Load environment variables before importing project modules.
load_dotenv()

from company_financials import get_company_financial_information
from database import Base, engine, get_db
from models import User
from password import hash_password, verify_password
from routers.company import router as company_router
from routers.news import router as news_router
from stock_data import get_historical_stock_data

logger = logging.getLogger(__name__)

# Create database tables.
Base.metadata.create_all(bind=engine)

# Initialize FastAPI.
app = FastAPI(
    title="AI-Powered Stock Research System",
    description="Stock research, historical data, financial information and AI news analysis.",
    version="1.0.0",
)

# CORS configuration.
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers.
app.include_router(company_router)
app.include_router(news_router)


# Request schemas.
class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# Validate stock ticker symbols.
def validate_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()

    if not re.fullmatch(r"[A-Z0-9.^=_-]{1,20}", ticker):
        raise HTTPException(
            status_code=400,
            detail="Invalid stock ticker format.",
        )

    return ticker


# -----------------------------
# USER REGISTRATION
# -----------------------------
@app.post("/register")
def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    username = payload.username.strip()
    email = str(payload.email).strip().lower()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty.",
        )

    try:
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email is already registered.",
            )

        new_user = User(
            username=username,
            email=email,
            hashed_password=hash_password(payload.password),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "Registration successful.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
            },
        }

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email is already registered.",
        ) from None

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during registration")

        raise HTTPException(
            status_code=500,
            detail="Unable to complete registration.",
        ) from None


# -----------------------------
# USER LOGIN
# -----------------------------
@app.post("/login")
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(
            payload.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error during login")

        raise HTTPException(
            status_code=500,
            detail="Unable to complete login.",
        ) from None


# -----------------------------
# HISTORICAL STOCK DATA
# -----------------------------
@app.get("/historical/{ticker}")
def historical_stock_data(
    ticker: str,
    period: str = Query(
        "6mo",
        pattern="^(1mo|3mo|6mo|1y|2y|5y|max)$",
    ),
):
    ticker = validate_ticker(ticker)

    try:
        df = get_historical_stock_data(ticker, period)

        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for '{ticker}'.",
            )

        if "Close" not in df.columns:
            raise ValueError("Historical data does not contain Close prices.")

        close = df["Close"]

        # Simple Moving Average.
        df["SMA_20"] = close.rolling(window=20).mean()

        # Exponential Moving Average.
        df["EMA_12"] = close.ewm(
            span=12,
            adjust=False,
        ).mean()

        ema_26 = close.ewm(
            span=26,
            adjust=False,
        ).mean()

        # MACD.
        df["MACD"] = df["EMA_12"] - ema_26

        # RSI.
        delta = close.diff()

        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()

        rs = gain / loss.replace(0, np.nan)

        df["RSI_14"] = 100 - (100 / (1 + rs))

        # Handle zero-loss conditions.
        df.loc[(loss == 0) & (gain > 0), "RSI_14"] = 100
        df.loc[(loss == 0) & (gain == 0), "RSI_14"] = 50

        # Convert NaN and infinite values into JSON-safe null values.
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.astype(object).where(df.notna(), None)

        records = df.to_dict(orient="records")

        # Convert timestamps into strings for JSON serialization.
        for record in records:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return {
            "success": True,
            "ticker": ticker,
            "period": period,
            "data": records,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unable to retrieve historical data for %s",
            ticker,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve historical stock data.",
        ) from None


# -----------------------------
# COMPANY FINANCIAL INFORMATION
# -----------------------------
@app.get("/financials/{ticker}")
def company_financials(ticker: str):
    ticker = validate_ticker(ticker)

    try:
        result = get_company_financial_information(ticker)

        if not isinstance(result, dict) or not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=(
                    result.get(
                        "message",
                        "Unable to retrieve company financial information.",
                    )
                    if isinstance(result, dict)
                    else "Invalid financial information response."
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unable to retrieve financial information for %s",
            ticker,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve company financial information.",
        ) from None


# -----------------------------
# ROOT / HEALTH CHECK
# -----------------------------
@app.get("/")
def root():
    return {
        "success": True,
        "message": "AI-Powered Stock Research System API is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "success": True,
        "status": "healthy",
    }
