import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries

logger = logging.getLogger("api_agent")
logging.basicConfig(level=logging.INFO)
load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
app = FastAPI(title="API Agent – Full Market Data (AV+YF)")

class StockRequest(BaseModel):
    symbols: List[str]
    history: bool = False
    period: str = "5d"
    interval: str = "1d"
    info: bool = False
    dividends: bool = False
    splits: bool = False
    financials: bool = False
    corporate_actions: bool = False  # Now ignored for optimization

class StockResponse(BaseModel):
    symbol: str
    latest_price: Optional[float] = None
    latest_timestamp: Optional[str] = None
    ohlcv_history: Optional[List[dict]] = None
    info: Optional[dict] = None
    dividends: Optional[List[dict]] = None
    splits: Optional[List[dict]] = None
    financials: Optional[dict] = None
    # corporate_actions REMOVED for optimization

class MultiStockResponse(BaseModel):
    results: List[StockResponse]

def av_get_timeseries(symbol, function, **kwargs):
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("Alpha Vantage API key not set")
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
    try:
        if function == "INTRADAY":
            data, meta = ts.get_intraday(symbol=symbol, interval=kwargs.get('interval', '5min'))
        elif function == "DAILY":
            data, meta = ts.get_daily(symbol=symbol)
        else:
            raise ValueError("Unknown AV function")
        return data
    except Exception as e:
        logger.warning(f"AV timeseries {function} failed for {symbol}: {e}")
        return None

def av_latest_from_ohlcv(data):
    if not data:
        return None, None
    times = sorted(data.keys())
    latest_time = times[-1]
    price = float(data[latest_time]['4. close'])
    return price, latest_time

@app.post("/quote", response_model=MultiStockResponse)
async def get_full_data(req: StockRequest):
    all_results = []
    for symbol in req.symbols:
        result = {"symbol": symbol.upper()}
        av_ohlcv = None
        av_price = None
        av_time = None
        if ALPHA_VANTAGE_API_KEY:
            av_ohlcv = av_get_timeseries(symbol, "INTRADAY")
            av_price, av_time = av_latest_from_ohlcv(av_ohlcv)
            if av_price is not None:
                result["latest_price"] = round(av_price, 2)
                result["latest_timestamp"] = av_time
            # Provide only 5 most recent OHLCV rows if requested
            if req.history and av_ohlcv:
                data_points = []
                for dt, v in list(av_ohlcv.items())[:5]:  # Only 5 days
                    row = {
                        "date": dt,
                        "open": float(v['1. open']),
                        "high": float(v['2. high']),
                        "low": float(v['3. low']),
                        "close": float(v['4. close']),
                        "volume": float(v['5. volume']),
                    }
                    data_points.append(row)
                result["ohlcv_history"] = data_points
        ticker = yf.Ticker(symbol)
        try:
            if result.get("latest_price") is None:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    latest = hist.iloc[-1]
                    result["latest_price"] = round(latest["Close"], 2)
                    result["latest_timestamp"] = str(latest.name)
            if req.history and (not result.get("ohlcv_history")):
                hist = ticker.history(period="5d", interval="1d")
                result["ohlcv_history"] = hist.reset_index().tail(2).to_dict("records")
            if req.info:
                info = ticker.info
                # Only return limited essential fields
                result["info"] = {k: info[k] for k in [
                    "longName", "sector", "industry", "currency", "exchange", "country", "website"
                ] if k in info}
            if req.dividends:
                divs = ticker.dividends.reset_index().tail(3).to_dict("records")
                result["dividends"] = divs
            if req.splits:
                splits = ticker.splits.reset_index().tail(3).to_dict("records")
                result["splits"] = splits
            if req.financials:
                # Limit to last 5 rows for each financial report
                result["financials"] = {
                    "income_statement": ticker.financials.iloc[:, :3].to_dict() if not ticker.financials.empty else {},
                    "balance_sheet": ticker.balance_sheet.iloc[:, :3].to_dict() if not ticker.balance_sheet.empty else {},
                    "cashflow": ticker.cashflow.iloc[:, :3].to_dict() if not ticker.cashflow.empty else {}
                }
            # Do not fetch corporate actions for optimization!
        except Exception as e:
            logger.warning(f"yfinance fallback failed for {symbol}: {e}")
        all_results.append(StockResponse(**result))
    return MultiStockResponse(results=all_results)
