import pytest
from app.services.news_service import NewsService
from app.api.routes.ai import calculate_trader_targets

def test_news_sentiment_breakdown():
    class MockNews:
        def __init__(self, sentiment_label):
            class Sentiment:
                sentiment = sentiment_label
            self.sentiment = Sentiment()

    items = [
        MockNews("positive"),
        MockNews("positive"),
        MockNews("positive"),
        MockNews("neutral"),
        MockNews("negative")
    ]
    breakdown = NewsService.calculate_news_sentiment_breakdown("XAUUSD", items)
    assert breakdown["bias"] == "BULLISH"
    assert breakdown["bullish"] == 60.0
    assert breakdown["bearish"] == 20.0
    assert breakdown["neutral"] == 20.0

def test_news_technical_confirmation():
    # Full bullish alignment
    confirm = NewsService.evaluate_news_technical_confirmation("bullish", "BULLISH", "LOW")
    assert confirm["status"] == "CONFIRMATION"
    assert confirm["score_multiplier"] > 1.0

    # Conflict test
    conflict = NewsService.evaluate_news_technical_confirmation("bullish", "BEARISH", "LOW")
    assert conflict["status"] == "CONFLICT"
    assert conflict["score_multiplier"] < 1.0

    # High-impact news event in proximity
    high_risk = NewsService.evaluate_news_technical_confirmation("bullish", "BULLISH", "HIGH")
    assert high_risk["status"] == "HIGH_RISK"
    assert high_risk["score_multiplier"] < 0.70

def test_trader_target_calculations():
    # Gold targets
    sl, tp1, tp2, tp3, rr, sl_dist, tp1_dist, tp2_dist, tp3_dist = calculate_trader_targets(
        symbol="XAUUSD",
        current_price=2650.0,
        direction="BUY",
        atr=8.0,
        precision=2
    )

    assert sl == 2641.50 # 2650 - 8.5
    assert tp1 == 2656.50 # +6.5
    assert tp2 == 2670.00 # +20.0
    assert tp3 == 2680.00 # +30.0
    assert rr >= 2.0
