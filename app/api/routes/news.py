from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import News, NewsSentiment
from app.schemas.schemas import NewsOut, NewsSentimentOut
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["News & Sentiment"])

@router.get("/", response_model=List[NewsOut])
def get_news_feed(
    language: str = Query("en", regex="^(en|km)$"),
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    news_items = NewsService.get_news(db, language=language, category=category, symbol=symbol, limit=limit)
    
    result = []
    for item in news_items:
        sent_out = None
        if item.sentiment:
            sent_out = NewsSentimentOut(
                sentiment=item.sentiment.sentiment,
                score=item.sentiment.score,
                confidence=item.sentiment.confidence,
                reasoning=item.sentiment.reasoning
            )
        
        result.append(NewsOut(
            id=item.id,
            title=item.title,
            summary=item.summary,
            content=item.content,
            source=item.source,
            url=item.url,
            language=item.language,
            category=item.category,
            impact=item.impact,
            affected_symbols_json=item.affected_symbols_json or [],
            published_at=item.published_at,
            sentiment=sent_out
        ))

    return result

@router.get("/calendar")
def get_economic_calendar(symbol: str = Query("XAUUSD")):
    events = NewsService.get_economic_calendar(symbol)
    risk_info = NewsService.check_economic_event_risk(symbol)
    return {
        "symbol": symbol.upper(),
        "news_risk": risk_info.get("news_risk"),
        "warning": risk_info.get("warning"),
        "events": [e.dict() if hasattr(e, "dict") else e for e in events]
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

    sent_out = None
    if item.sentiment:
        sent_out = NewsSentimentOut(
            sentiment=item.sentiment.sentiment,
            score=item.sentiment.score,
            confidence=item.sentiment.confidence,
            reasoning=item.sentiment.reasoning
        )

    return NewsOut(
        id=item.id,
        title=item.title,
        summary=item.summary,
        content=item.content,
        source=item.source,
        url=item.url,
        language=item.language,
        category=item.category,
        impact=item.impact,
        affected_symbols_json=item.affected_symbols_json or [],
        published_at=item.published_at,
        sentiment=sent_out
    )
