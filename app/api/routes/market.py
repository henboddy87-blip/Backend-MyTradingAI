from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.market import get_market_data_provider
from app.models.models import Asset
from app.schemas.schemas import MarketTickerItem, MarketCandleOut, AssetOut

router = APIRouter(prefix="/market", tags=["Market Data"])

@router.get("/tickers", response_model=List[MarketTickerItem])
def get_tickers():
    provider = get_market_data_provider()
    return provider.get_all_tickers()

@router.get("/ticker/{symbol}", response_model=MarketTickerItem)
def get_ticker(symbol: str):
    provider = get_market_data_provider()
    return provider.get_ticker(symbol.upper())

@router.get("/candles/{symbol}", response_model=List[MarketCandleOut])
def get_candles(
    symbol: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|30m|1h|4h|1d)$"),
    limit: int = Query(100, ge=10, le=500)
):
    provider = get_market_data_provider()
    return provider.get_historical_candles(symbol.upper(), timeframe=timeframe, limit=limit)

@router.get("/assets", response_model=List[AssetOut])
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).filter(Asset.is_active == True).all()

@router.get("/overview")
def get_market_overview(db: Session = Depends(get_db)):
    provider = get_market_data_provider()
    tickers = provider.get_all_tickers()
    
    categories = {
        "crypto": [],
        "forex": [],
        "commodity": [],
        "stock": [],
        "index": []
    }
    
    for t in tickers:
        m_type = t.get("market_type", "crypto")
        if m_type in categories:
            categories[m_type].append(t)
        else:
            categories["crypto"].append(t)

    return {
        "categories": categories,
        "total_assets": len(tickers),
        "data_mode": "mock",
        "timestamp": tickers[0]["timestamp"] if tickers else None
    }
