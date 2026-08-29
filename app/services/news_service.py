import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import News, NewsSentiment
from app.schemas.schemas import EconomicEventItem
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

    @classmethod
    def calculate_news_sentiment_breakdown(cls, symbol: str, news_items: List[News]) -> Dict[str, Any]:
        """
        Calculates sentiment distribution (Bullish %, Bearish %, Neutral %) and sentiment strength.
        Example: { "bullish": 72, "bearish": 18, "neutral": 10, "bias": "BULLISH", "strength": 0.72 }
        """
        if not news_items:
            return {
                "bullish": 33.3,
                "bearish": 33.3,
                "neutral": 33.4,
                "bias": "NEUTRAL",
                "strength": 0.50,
                "headline_count": 0
            }

        pos_count = 0
        neg_count = 0
        neu_count = 0

        for item in news_items:
            sent = item.sentiment.sentiment if item.sentiment else "neutral"
            if sent == "positive":
                pos_count += 1
            elif sent == "negative":
                neg_count += 1
            else:
                neu_count += 1

        total = max(1, len(news_items))
        pos_pct = round((pos_count / total) * 100.0, 1)
        neg_pct = round((neg_count / total) * 100.0, 1)
        neu_pct = round((neu_count / total) * 100.0, 1)

        if pos_pct > neg_pct + 15:
            bias = "BULLISH"
            strength = round(pos_pct / 100.0, 2)
        elif neg_pct > pos_pct + 15:
            bias = "BEARISH"
            strength = round(neg_pct / 100.0, 2)
        else:
            bias = "NEUTRAL"
            strength = 0.50

        return {
            "bullish": pos_pct,
            "bearish": neg_pct,
            "neutral": neu_pct,
            "bias": bias,
            "strength": strength,
            "headline_count": total
        }

    @classmethod
    def get_economic_calendar(cls, symbol: str) -> List[EconomicEventItem]:
        """
        Maps institutional economic calendar events:
        CPI, PPI, NFP, FOMC, Fed speeches, Interest Rate decisions, GDP, Unemployment, Retail Sales, PMI, Crude inventory.
        """
        symbol_upper = symbol.upper()
        events = [
            EconomicEventItem(
                title="US Core Consumer Price Index (CPI MoM)",
                impact="HIGH",
                currency="USD",
                time_label="Tomorrow 12:30 GMT",
                is_approaching=True,
                risk_level="HIGH" if "USD" in symbol_upper or "XAU" in symbol_upper or "NAS" in symbol_upper else "MODERATE"
            ),
            EconomicEventItem(
                title="FOMC Interest Rate Decision & Press Conference",
                impact="HIGH",
                currency="USD",
                time_label="Next Week 18:00 GMT",
                is_approaching=False,
                risk_level="HIGH"
            ),
            EconomicEventItem(
                title="US Non-Farm Payrolls (NFP) & Unemployment Rate",
                impact="HIGH",
                currency="USD",
                time_label="Friday 12:30 GMT",
                is_approaching=True,
                risk_level="HIGH"
            ),
            EconomicEventItem(
                title="EIA Crude Oil Inventory Report",
                impact="MEDIUM",
                currency="USD",
                time_label="Wednesday 14:30 GMT",
                is_approaching=True,
                risk_level="HIGH" if "OIL" in symbol_upper else "LOW"
            )
        ]
        return events

    @classmethod
    def check_economic_event_risk(cls, symbol: str) -> Dict[str, Any]:
        """
        Evaluates whether high-impact events pose imminent news risk.
        Returns: { "news_risk": "HIGH" | "MODERATE" | "LOW", "is_approaching": bool, "warning": str }
        """
        events = cls.get_economic_calendar(symbol)
        high_impact_approaching = [e for e in events if e.impact == "HIGH" and e.is_approaching]

        if high_impact_approaching:
            return {
                "news_risk": "HIGH",
                "is_approaching": True,
                "event_title": high_impact_approaching[0].title,
                "time_label": high_impact_approaching[0].time_label,
                "warning": f"High-Impact event approaching: {high_impact_approaching[0].title} ({high_impact_approaching[0].time_label}). Widen risk buffer or stand aside."
            }
        else:
            return {
                "news_risk": "LOW",
                "is_approaching": False,
                "event_title": None,
                "time_label": None,
                "warning": "No imminent high-impact economic releases within proximity."
            }

    @classmethod
    def evaluate_news_technical_confirmation(
        cls,
        tech_bias: str,
        news_bias: str,
        news_risk: str
    ) -> Dict[str, Any]:
        """
        Cross-confirms technical bias with news flow:
        - CONFIRMATION: Tech Bullish + News Bullish (High conviction)
        - NEUTRAL: Tech Bullish + News Neutral (Standard trade)
        - CONFLICT: Tech Bullish + News Bearish (Divergence -> Caution / Lower score)
        - HIGH_RISK: High-impact news event in proximity -> Enforce WAIT!
        """
        tech_b = tech_bias.upper()
        news_b = news_bias.upper()

        if news_risk == "HIGH":
            status = "HIGH_RISK"
            multiplier = 0.65
            reason = "High-impact macroeconomic event in proximity creates asymmetric news risk. Enforcing capital preservation."
        elif tech_b == news_b and tech_b in ["BULLISH", "BEARISH"]:
            status = "CONFIRMATION"
            multiplier = 1.15
            reason = f"Full alignment: Technical {tech_b} structure confirmed by {news_b} news sentiment."
        elif news_b == "NEUTRAL":
            status = "NEUTRAL"
            multiplier = 1.00
            reason = f"Technical {tech_b} setup with balanced, neutral news background."
        else:
            status = "CONFLICT"
            multiplier = 0.70
            reason = f"Divergence detected: Technical {tech_b} conflicts with {news_b} news sentiment. Reduce confidence."

        return {
            "status": status,
            "score_multiplier": multiplier,
            "reasoning": reason
        }
