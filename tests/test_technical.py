from app.services.technical_analysis import TechnicalAnalysisService

def test_rsi_calculation():
    # Monotonically increasing prices should have high RSI > 70
    increasing = [100.0 + i * 2.0 for i in range(30)]
    rsi_high = TechnicalAnalysisService.calculate_rsi(increasing, 14)
    assert rsi_high > 70.0

    # Monotonically decreasing prices should have low RSI < 30
    decreasing = [100.0 - i * 2.0 for i in range(30)]
    rsi_low = TechnicalAnalysisService.calculate_rsi(decreasing, 14)
    assert rsi_low < 30.0

def test_ema_calculation():
    prices = [10.0] * 20
    ema = TechnicalAnalysisService.calculate_ema(prices, 10)
    assert round(ema, 2) == 10.0

def test_macd_calculation():
    prices = [100.0 + (i % 5) * 2.0 for i in range(50)]
    macd = TechnicalAnalysisService.calculate_macd(prices)
    assert hasattr(macd, "value")
    assert hasattr(macd, "signal")
    assert hasattr(macd, "histogram")

def test_full_technical_analysis():
    candles = [
        {"open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i, "volume": 1000}
        for i in range(40)
    ]
    res = TechnicalAnalysisService.analyze("BTCUSDT", "1h", candles)
    assert res.symbol == "BTCUSDT"
    assert res.rsi > 0
    assert res.trend in ["bullish", "bearish", "neutral"]
    assert res.atr > 0
