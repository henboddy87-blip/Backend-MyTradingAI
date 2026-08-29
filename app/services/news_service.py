import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import News, NewsSentiment
from app.core.logging import logger

class NewsService:
    @staticmethod
    def analyze_sentiment(title: str, summary: str) -> Dict[str, Any]:
        """
        Calculates sentiment classification and score from financial news text.
        """
        text = f"{title} {summary}".lower()
        
        bullish_keywords = [
            "surge", "rally", "gain", "bullish", "growth", "high", "positive",
            "record", "inflow", "accumulate", "jump", "boost", "optimism", "expansion", "profit"
        ]
        bearish_keywords = [
            "drop", "fall", "bearish", "decline", "crash", "plunge", "loss",
            "negative", "inflation", "hike", "recession", "tension", "risk", "warning", "ban"
        ]

        bull_count = sum(1 for kw in bullish_keywords if kw in text)
        bear_count = sum(1 for kw in bearish_keywords if kw in text)

        if bull_count > bear_count:
            sentiment = "positive"
            score = min(0.95, 0.4 + (bull_count * 0.15))
            confidence = min(92.0, 60.0 + (bull_count * 8.0))
            reasoning = f"Dominant positive terminology ({bull_count} bullish indicators detected)."
        elif bear_count > bull_count:
            sentiment = "negative"
            score = max(-0.95, -0.4 - (bear_count * 0.15))
            confidence = min(92.0, 60.0 + (bear_count * 8.0))
            reasoning = f"Dominant cautionary or adverse factors ({bear_count} bearish risk factors detected)."
        else:
            sentiment = "neutral"
            score = 0.0
            confidence = 65.0
            reasoning = "Balanced macroeconomic context with neutral short-term directional bias."

        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "confidence": round(confidence, 1),
            "reasoning": reasoning
        }

    @classmethod
    def get_news(
        cls,
        db: Session,
        language: str = "en",
        category: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 20
    ) -> List[News]:
        query = db.query(News)
        if language:
            query = query.filter(News.language == language)
        if category and category.lower() != "all":
            query = query.filter(News.category.ilike(f"%{category}%"))
        
        items = query.order_by(News.published_at.desc()).limit(limit).all()

        if symbol:
            symbol = symbol.upper()
            filtered = []
            for item in items:
                symbols = item.affected_symbols_json or []
                if symbol in symbols or not symbols:
                    filtered.append(item)
            return filtered

        return items
