from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from company_financials import get_company_financial_information
from database import Base, engine, get_db
from models import User
from password import hash_password, verify_password
from routers import company
from stock_data import get_historical_stock_data

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Stock Research System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /companies/search router
app.include_router(company.router)


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/register")
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    if not payload.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    existing_user = db.query(User).filter(User.email == payload.email.strip()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    new_user = User(
        username=payload.username.strip(),
        email=payload.email.strip(),
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


@app.post("/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    }


@app.get("/historical/{ticker}")
def historical_stock_data(
    ticker: str,
    period: str = Query("6mo", pattern="^(1mo|3mo|6mo|1y|2y|5y|max)$"),
):
    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker cannot be empty.")

    try:
        df = get_historical_stock_data(ticker.strip(), period)
        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for '{ticker.strip()}'.",
            )

        # Compute technical indicators expected by HistoricalData.jsx
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA_12"] - ema_26

        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI_14"] = 100 - (100 / (1 + rs))

        # Replace NaN/Inf with None so JSON serialization succeeds cleanly
        df = df.replace([np.nan, np.inf, -np.inf], None)

        return {
            "success": True,
            "ticker": ticker.strip(),
            "period": period,
            "data": df.to_dict(orient="records"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve historical data: {e!s}",
        ) from e


@app.get("/financials/{ticker}")
def company_financials(ticker: str):
    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker cannot be empty.")

    try:
        result = get_company_financial_information(ticker.strip())
        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message", "Unable to retrieve company financial information."
                ),
            )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve financial information: {e!s}",
        ) from e
