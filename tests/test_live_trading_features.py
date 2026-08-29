import pytest
from app.models.models import User
from app.core.security import get_password_hash
from app.auth.jwt import create_access_token
from app.market.live_provider import LiveMarketDataProvider
from app.services.technical_analysis import TechnicalAnalysisService
from app.schemas.schemas import PivotPointsResult, TechnicalGaugeResult

def test_live_market_provider():
    provider = LiveMarketDataProvider()
    # Test ticker
    btc_ticker = provider.get_ticker("BTCUSDT")
    assert btc_ticker is not None
    assert "price" in btc_ticker
    assert btc_ticker["price"] > 0
    assert "change_24h" in btc_ticker

    # Test candles
    btc_candles = provider.get_historical_candles("BTCUSDT", "1h", limit=20)
    assert len(btc_candles) >= 10
    assert "open" in btc_candles[0]
    assert "high" in btc_candles[0]
    assert "low" in btc_candles[0]
    assert "close" in btc_candles[0]
    assert "volume" in btc_candles[0]

def test_pivot_points_calculation():
    sample_candles = [
        {"time": 1000 + i*3600, "open": 2000.0, "high": 2050.0, "low": 1980.0, "close": 2020.0, "volume": 500}
        for i in range(24)
    ]
    pivots = TechnicalAnalysisService.calculate_pivot_points(sample_candles)
    assert isinstance(pivots, PivotPointsResult)
    assert pivots.classic.pivot > 0
    assert pivots.classic.r1 > pivots.classic.pivot
    assert pivots.classic.s1 < pivots.classic.pivot
    assert pivots.fibonacci.r2 > pivots.fibonacci.r1
    assert pivots.camarilla.r3 > pivots.camarilla.r1

def test_candlestick_pattern_detection():
    sample_candles = [
        {"time": 1000, "open": 2000.0, "high": 2010.0, "low": 1990.0, "close": 2005.0, "volume": 100},
        {"time": 2000, "open": 2005.0, "high": 2006.0, "low": 1980.0, "close": 1982.0, "volume": 200},
        {"time": 3000, "open": 1980.0, "high": 2015.0, "low": 1978.0, "close": 2012.0, "volume": 500},
    ]
    patterns = TechnicalAnalysisService.detect_candlestick_patterns(sample_candles)
    assert len(patterns) >= 1
    assert any(p.pattern_type in ["BULLISH", "BEARISH", "NEUTRAL"] for p in patterns)

def test_technical_gauge_calculation():
    sample_candles = [
        {"time": 1000 + i*3600, "open": 2000.0 + i*2, "high": 2010.0 + i*2, "low": 1990.0 + i*2, "close": 2005.0 + i*2, "volume": 1000}
        for i in range(50)
    ]
    tech = TechnicalAnalysisService.analyze("XAUUSD", "1h", sample_candles)
    closes = [c["close"] for c in sample_candles]
    gauge = TechnicalAnalysisService.calculate_technical_gauge(tech, closes, closes[-1])
    assert isinstance(gauge, TechnicalGaugeResult)
    assert gauge.overall.summary in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
    assert 0 <= gauge.score_percentage <= 100

def test_market_deep_analysis_endpoint(client):
    response = client.get("/api/v1/market/analysis/BTCUSDT?timeframe=1h")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert "current_price" in data
    assert "pivots" in data
    assert "gauge" in data
    assert "patterns" in data
    assert "mtf_radar" in data
    assert "fear_and_greed" in data
    assert data["pivots"]["classic"]["pivot"] > 0

def test_live_signal_generation_endpoint(client, db_session):
    user = User(
        full_name="Live Signal Tester",
        username="signal_tester",
        email="signaltester@example.com",
        password_hash=get_password_hash("Pass123!"),
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": str(user.id), "username": user.username, "role": "USER"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/signals/generate-live?symbol=BTCUSDT&timeframe=1h&risk_level=Medium", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["direction"] in ["BUY", "SELL", "NO_TRADE"]
    assert "confidence" in data
    assert "reasoning" in data

def test_execute_live_trade_endpoint(client, db_session):
    user = User(
        full_name="Live Trade Tester",
        username="trade_tester",
        email="tradetester@example.com",
        password_hash=get_password_hash("Pass123!"),
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token({"sub": str(user.id), "username": user.username, "role": "USER"})
    headers = {"Authorization": f"Bearer {token}"}

    trade_payload = {
        "symbol": "BTCUSDT",
        "direction": "BUY",
        "timeframe": "1h",
        "entry_price": 75000.0,
        "stop_loss": 74200.0,
        "take_profit": 77000.0,
        "position_size": 0.5,
        "notes": "Live paper trade execution test"
    }
    response = client.post("/api/v1/journal/execute-trade", json=trade_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["direction"] == "BUY"
    assert data["outcome"] == "OPEN"
    trade_id = data["id"]

    # Now close the position
    close_resp = client.post(f"/api/v1/journal/close-position/{trade_id}?exit_price=76000.0", headers=headers)
    assert close_resp.status_code == 200
    close_data = close_resp.json()
    assert close_data["outcome"] == "WIN"
    assert close_data["profit_loss"] == 500.0
