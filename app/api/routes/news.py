from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import News, NewsSentiment
from app.schemas.schemas import NewsOut, NewsSentimentOut, NewsSignalCatalystOut, NewsSyncResponse, SignalOut, NewsSignalGenerateRequest
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["News & Sentiment"])

def _map_news_out(item: News) -> NewsOut:
    sent_out = None
    if item.sentiment:
        sent_out = NewsSentimentOut(
            sentiment=item.sentiment.sentiment,
            score=float(item.sentiment.score),
            confidence=float(item.sentiment.confidence),
            reasoning=item.sentiment.reasoning
        )
    
    catalyst_data = NewsService.get_news_signal_catalyst(item)
    catalyst_out = NewsSignalCatalystOut(
        bias=catalyst_data["bias"],
        confluence_boost=catalyst_data["confluence_boost"],
        setup_type=catalyst_data["setup_type"],
        primary_symbol=catalyst_data["primary_symbol"],
        action_label=catalyst_data["action_label"],
        reasoning=catalyst_data["reasoning"]
    )

    time_ago_str = NewsService.format_time_ago(item.published_at)

    return NewsOut(
        id=int(item.id),
        title=str(item.title),
        summary=str(item.summary),
        content=str(item.content) if item.content is not None else None,
        source=str(item.source),
        url=str(item.url) if item.url is not None else None,
        language=str(item.language),
        category=str(item.category),
        impact=str(item.impact),
        affected_symbols_json=list(item.affected_symbols_json or []),
        published_at=item.published_at,
        time_ago=time_ago_str,
        signal_catalyst=catalyst_out,
        sentiment=sent_out
    )

@router.get("/", response_model=List[NewsOut])
def get_news_feed(
    language: str = Query("en", pattern="^(en|km)$"),
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    news_items = NewsService.get_news(db, language=language, category=category, symbol=symbol, limit=limit)
    return [_map_news_out(item) for item in news_items]

@router.post("/sync", response_model=NewsSyncResponse)
def sync_live_news_feed(db: Session = Depends(get_db)):
    """
    Manually triggers live real-time institutional feed sync from global financial wires.
    """
    count = NewsService.sync_live_news(db, max_per_feed=8)
    total = db.query(News).count()
    return NewsSyncResponse(
        status="success",
        message=f"Synced {count} fresh market intelligence reports into institutional stream.",
        synced_count=count,
        total_news=total
    )

@router.post("/generate-signal-from-news", response_model=SignalOut)
def generate_signal_from_news_endpoint(
    request: NewsSignalGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates an active institutional trading signal derived directly from a specific news headline catalyst.
    """
    try:
        signal = NewsService.generate_signal_from_news(
            db=db,
            news_id=request.news_id,
            symbol=request.symbol,
            timeframe=request.timeframe,
            risk_level=request.risk_level
        )
        return signal
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signal from news catalyst: {str(e)}")

@router.post("/batch-generate-signals", response_model=List[SignalOut])
def batch_generate_news_signals(
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Scans latest high-impact news updates and generates corresponding trading signals across multiple asset classes.
    """
    signals = NewsService.generate_batch_signals_from_news(db, limit=limit)
    return signals

@router.get("/calendar")
def get_economic_calendar(symbol: str = Query("XAUUSD")):
    events = NewsService.get_economic_calendar(symbol)
    risk_info = NewsService.check_economic_event_risk(symbol)
    return {
        "symbol": symbol.upper(),
        "news_risk": risk_info.get("news_risk"),
        "warning": risk_info.get("warning"),
        "events": [e.model_dump() if hasattr(e, "model_dump") else (e.dict() if hasattr(e, "dict") else e) for e in events]
    }

@router.get("/sentiment-overview")
def get_market_sentiment_overview(
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    news_items = NewsService.get_news(db, language="en", symbol=symbol, limit=20)
    sentiment_data = NewsService.calculate_news_sentiment_breakdown(symbol or "ALL", news_items)
    return sentiment_data

@router.get("/{id}", response_model=NewsOut)
def get_single_news(id: int, db: Session = Depends(get_db)):
    item = db.query(News).filter(News.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")

    return _map_news_out(item)

