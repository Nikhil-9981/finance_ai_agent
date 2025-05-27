# agents/api_agent/main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
from dotenv import load_dotenv

# Load any .env variables (e.g. API keys later)
load_dotenv()

app = FastAPI(title="API Agent – Market Data")

class QuoteRequest(BaseModel):
    symbol: str

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str

@app.post("/quote", response_model=QuoteResponse)
async def get_quote(req: QuoteRequest):
    ticker = yf.Ticker(req.symbol)
    data = ticker.history(period="1d")
    if data.empty:
        raise HTTPException(status_code=404, detail="Symbol not found")
    latest = data.iloc[-1]
    return QuoteResponse(
        symbol=req.symbol.upper(),
        price=round(latest["Close"], 2),
        timestamp=latest.name.isoformat()
    )



