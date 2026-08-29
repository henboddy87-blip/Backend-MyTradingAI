import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.core.database import get_db
from app.market import get_market_data_provider
from app.models.models import Asset
from app.schemas.schemas import (
    MarketTickerItem, MarketCandleOut, AssetOut,
    MarketDeepAnalysisOut
)
from app.services.technical_analysis import TechnicalAnalysisService

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
    timeframe: str = Query("1h", pattern="^(1m|5m|15m|30m|1h|4h|1d)$"),
    limit: int = Query(100, ge=10, le=500)
):
    provider = get_market_data_provider()
    return provider.get_historical_candles(symbol.upper(), timeframe=timeframe, limit=limit)

@router.get("/assets", response_model=List[AssetOut])
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).filter(Asset.is_active == True).all()

@router.get("/fear-and-greed")
def get_fear_and_greed():
    provider = get_market_data_provider()
    if hasattr(provider, "get_fear_and_greed_index"):
        return provider.get_fear_and_greed_index()
    return {
        "value": 68,
        "classification": "Greed",
        "timestamp": str(int(datetime.datetime.now().timestamp())),
        "history": []
    }

@router.get("/analysis/{symbol}", response_model=MarketDeepAnalysisOut)
def get_deep_market_analysis(
    symbol: str,
    timeframe: str = Query("1h", pattern="^(1m|5m|15m|30m|1h|4h|1d)$"),
    db: Session = Depends(get_db)
):
    symbol = symbol.upper()
    provider = get_market_data_provider()
    
    # 1. Fetch live ticker & candles
    ticker = provider.get_ticker(symbol)
    candles = provider.get_historical_candles(symbol, timeframe=timeframe, limit=120)
    
    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    name = asset.name if asset and asset.name else str(ticker.get("name", symbol))
    market_type = asset.market_type if asset and asset.market_type else str(ticker.get("market_type", "crypto"))
    current_price: float = float(ticker.get("price") or (candles[-1]["close"] if candles else 100.0))

    # 2. Compute technical analysis suite
    tech = TechnicalAnalysisService.analyze(symbol, timeframe, candles)
    closes = [c["close"] for c in candles] if candles else [current_price]

    # 3. Calculate Pivots, Gauge, Patterns, Order Blocks & SMC Suite
    pivots = TechnicalAnalysisService.calculate_pivot_points(candles)
    patterns = TechnicalAnalysisService.detect_candlestick_patterns(candles)
    order_blocks = TechnicalAnalysisService.detect_order_blocks(candles, timeframe=timeframe)
    fair_value_gaps = TechnicalAnalysisService.detect_fair_value_gaps(candles, timeframe=timeframe)
    liquidity_sweeps = TechnicalAnalysisService.detect_liquidity_sweeps(candles, timeframe=timeframe)
    smc = TechnicalAnalysisService.calculate_smart_money_concepts(candles, timeframe=timeframe, current_price=current_price)
    gauge = TechnicalAnalysisService.calculate_technical_gauge(tech, closes, current_price)

    # 4. Multi-Timeframe Radar across 1m, 5m, 15m, 1h, 4h, 1d
    radar_tfs = ["1m", "5m", "15m", "1h", "4h", "1d"]
    mtf_radar = {}
    for tf in radar_tfs:
        tf_candles = provider.get_historical_candles(symbol, timeframe=tf, limit=30)
        tf_tech = TechnicalAnalysisService.analyze(symbol, tf, tf_candles)
        if tf_tech.trend == "bullish" and tf_tech.rsi > 52:
            mtf_radar[tf] = "STRONG_BUY" if tf_tech.momentum == "strong" else "BUY"
        elif tf_tech.trend == "bearish" and tf_tech.rsi < 48:
            mtf_radar[tf] = "STRONG_SELL" if tf_tech.momentum == "strong" else "SELL"
        else:
            mtf_radar[tf] = "NEUTRAL"

    # 5. Fear & Greed
    fng = provider.get_fear_and_greed_index() if hasattr(provider, "get_fear_and_greed_index") else {"value": 68, "classification": "Greed"}

    return MarketDeepAnalysisOut(
        symbol=symbol,
        name=name,
        market_type=market_type,
        current_price=current_price,
        change_24h=float(ticker.get("change_24h") or 0.0),
        high_24h=float(ticker.get("high_24h") or (current_price * 1.02)),
        low_24h=float(ticker.get("low_24h") or (current_price * 0.98)),
        volume_24h=float(ticker.get("volume_24h") or 100000.0),
        timeframe=timeframe,
        technical=tech,
        pivots=pivots,
        gauge=gauge,
        patterns=patterns,
        order_blocks=order_blocks,
        fair_value_gaps=fair_value_gaps,
        liquidity_sweeps=liquidity_sweeps,
        smc=smc,
        mtf_radar=mtf_radar,
        fear_and_greed=fng,
        data_mode=settings.DATA_MODE,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

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

    # Sort each category by highest volume
    for cat in categories:
        categories[cat] = sorted(categories[cat], key=lambda x: x.get("volume_24h", 0), reverse=True)

    # Top Gainers & Losers across all tickers
    sorted_by_change = sorted(tickers, key=lambda x: x.get("change_24h", 0), reverse=True)
    top_gainers = sorted_by_change[:4]
    top_losers = sorted_by_change[-4:]

    return {
        "categories": categories,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "total_assets": len(tickers),
        "data_mode": settings.DATA_MODE,
        "timestamp": tickers[0]["timestamp"] if tickers else datetime.datetime.now(datetime.timezone.utc)
    }
