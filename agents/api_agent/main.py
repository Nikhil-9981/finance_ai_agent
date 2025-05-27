# agents/api_agent/main.py

import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries

logger = logging.getLogger("api_agent")

# Load .env variables
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

app = FastAPI(title="API Agent – Market Data")

class QuoteRequest(BaseModel):
    symbol: str

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str

def get_quote_alpha_vantage(symbol: str):
    """Try to get latest price from Alpha Vantage"""
    if not ALPHA_VANTAGE_API_KEY:
        logger.error("Alpha Vantage API key not set.")
        raise Exception("Alpha Vantage API key not set")
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
    # Try intraday first (for most recent), fallback to daily
    try:
        data, meta = ts.get_intraday(symbol=symbol, interval='5min', outputsize='compact')
        if data:
            latest_time = sorted(data.keys())[-1]
            price = float(data[latest_time]['4. close'])
            logger.info(f"Alpha Vantage INTRADAY success for {symbol}: {price} at {latest_time}")
            return price, latest_time
    except Exception as e:
        logger.warning(f"Alpha Vantage intraday fetch failed for {symbol}: {e}")
    try:
        data, meta = ts.get_daily(symbol=symbol, outputsize='compact')
        if data:
            latest_time = sorted(data.keys())[-1]
            price = float(data[latest_time]['4. close'])
            logger.info(f"Alpha Vantage DAILY success for {symbol}: {price} at {latest_time}")
            return price, latest_time
    except Exception as e:
        logger.error(f"Alpha Vantage daily fetch failed for {symbol}: {e}")
        raise Exception(f"Alpha Vantage fetch failed: {e}")
    logger.error(f"Alpha Vantage: No data found for symbol {symbol}")
    raise Exception("Alpha Vantage: No data found for symbol")

def get_quote_yfinance(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            logger.error(f"yfinance: No data found for {symbol}")
            raise Exception("yfinance: No data found")
        latest = data.iloc[-1]
        price = round(latest["Close"], 2)
        timestamp = latest.name.isoformat()
        logger.info(f"yfinance success for {symbol}: {price} at {timestamp}")
        return price, timestamp
    except Exception as e:
        logger.error(f"yfinance fetch failed for {symbol}: {e}")
        raise Exception(f"yfinance fetch failed: {e}")

@app.post("/quote", response_model=QuoteResponse)
async def get_quote(req: QuoteRequest):
    logger.info(f"Received quote request for symbol: {req.symbol}")
    # Try Alpha Vantage first
    try:
        price, timestamp = get_quote_alpha_vantage(req.symbol)
        logger.info(f"Returned Alpha Vantage price for {req.symbol}")
        return QuoteResponse(
            symbol=req.symbol.upper(),
            price=round(price, 2),
            timestamp=timestamp
        )
    except Exception as av_err:
        logger.warning(f"Alpha Vantage failed for {req.symbol}: {av_err}")
        # Fallback to yfinance
        try:
            price, timestamp = get_quote_yfinance(req.symbol)
            logger.info(f"Returned yfinance price for {req.symbol}")
            return QuoteResponse(
                symbol=req.symbol.upper(),
                price=round(price, 2),
                timestamp=timestamp
            )
        except Exception as yf_err:
            logger.error(
                f"Both Alpha Vantage and yfinance failed for {req.symbol} "
                f"(Alpha Vantage error: {av_err}, yfinance error: {yf_err})"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Symbol not found (Alpha Vantage error: {av_err}, yfinance error: {yf_err})"
            )
