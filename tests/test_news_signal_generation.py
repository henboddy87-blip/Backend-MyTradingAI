import datetime
from app.services.news_service import NewsService
from app.models.models import News, NewsSentiment, Asset
from app.api.routes.news import _map_news_out

def test_news_format_time_ago():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Just now
    assert NewsService.format_time_ago(now - datetime.timedelta(seconds=20)) == "Just now"
    # 5 minutes ago
    assert NewsService.format_time_ago(now - datetime.timedelta(minutes=5)) == "5m ago"
    # 3 hours ago
    assert NewsService.format_time_ago(now - datetime.timedelta(hours=3)) == "3h ago"
    # Yesterday
    assert NewsService.format_time_ago(now - datetime.timedelta(hours=28)) == "Yesterday"
    # 4 days ago
    assert NewsService.format_time_ago(now - datetime.timedelta(days=4)) == "4d ago"

def test_news_signal_catalyst_evaluation():
    news_bullish = News(
        id=1,
        title="Gold Surges to All-Time Highs on Strong Inflows",
        summary="Bullion breaks key resistance with institutional momentum.",
        affected_symbols_json=["XAUUSD"],
        impact="HIGH",
        published_at=datetime.datetime.now(datetime.timezone.utc)
    )
    news_bullish.sentiment = NewsSentiment(sentiment="positive", score=0.85, confidence=90.0)

    catalyst = NewsService.get_news_signal_catalyst(news_bullish)
    assert catalyst["bias"] == "BULLISH"
    assert "Confluence Boost" in catalyst["confluence_boost"]
    assert catalyst["primary_symbol"] == "XAUUSD"
    assert "BUY Catalyst on XAUUSD" in catalyst["action_label"]

    news_bearish = News(
        id=2,
        title="Tech Equities Drop Following Hawkish Central Bank Commentary",
        summary="Risk assets face distribution pressure.",
        affected_symbols_json=["NAS100"],
        impact="HIGH",
        published_at=datetime.datetime.now(datetime.timezone.utc)
    )
    news_bearish.sentiment = NewsSentiment(sentiment="negative", score=-0.65, confidence=85.0)

    catalyst_bear = NewsService.get_news_signal_catalyst(news_bearish)
    assert catalyst_bear["bias"] == "BEARISH"
    assert "Downside Pressure" in catalyst_bear["confluence_boost"]
    assert catalyst_bear["primary_symbol"] == "NAS100"

def test_news_api_endpoints(db_session, client):
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Create test asset
    existing_asset = db_session.query(Asset).filter(Asset.symbol == "XAUUSD").first()
    if not existing_asset:
        asset = Asset(
            symbol="XAUUSD",
            name="Gold / USD",
            market_type="commodity",
            base_currency="XAU",
            quote_currency="USD",
            pip_size=0.01,
            precision=2
        )
        db_session.add(asset)
        db_session.commit()

    # Create test news
    news = News(
        title="Gold Demand Spikes on Global Reserve Accumulation",
        summary="Central banks report massive gold purchases for international reserves.",
        source="Institutional Wire",
        language="en",
        category="Commodities",
        impact="HIGH",
        affected_symbols_json=["XAUUSD"],
        published_at=now - datetime.timedelta(minutes=10),
        created_at=now - datetime.timedelta(minutes=10)
    )
    db_session.add(news)
    db_session.flush()

    db_session.add(NewsSentiment(
        news_id=news.id,
        sentiment="positive",
        score=0.88,
        confidence=92.0,
        reasoning="Strong institutional accumulation metrics."
    ))
    db_session.commit()

    # Test GET /api/v1/news/
    response = client.get("/api/v1/news/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    first_item = next(item for item in data if item["id"] == news.id)
    assert first_item["time_ago"] == "10m ago"
    assert first_item["signal_catalyst"] is not None
    assert first_item["signal_catalyst"]["bias"] == "BULLISH"

    # Test POST /api/v1/news/sync
    sync_resp = client.post("/api/v1/news/sync")
    assert sync_resp.status_code == 200
    assert sync_resp.json()["status"] == "success"

    # Test POST /api/v1/news/generate-signal-from-news
    sig_resp = client.post("/api/v1/news/generate-signal-from-news", json={
        "news_id": news.id,
        "symbol": "XAUUSD",
        "timeframe": "1h",
        "risk_level": "Medium"
    })
    assert sig_resp.status_code == 200
    sig_data = sig_resp.json()
    assert sig_data["symbol"] == "XAUUSD"
    assert "News Catalyst" in sig_data["sentiment_summary"]

