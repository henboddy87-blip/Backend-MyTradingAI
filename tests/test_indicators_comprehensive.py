from app.services.technical_analysis import TechnicalAnalysisService

def test_ema_and_sma_calculations():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]
    ema_5 = TechnicalAnalysisService.calculate_ema(prices, 5)
    sma_5 = TechnicalAnalysisService.calculate_sma(prices, 5)

    assert ema_5 > 0
    assert sma_5 == 18.0 # (16+17+18+19+20)/5 = 18.0
    assert isinstance(ema_5, float)

def test_rsi_calculation():
    # Strong uptrend prices
    prices = [100 + i * 2 for i in range(30)]
    rsi = TechnicalAnalysisService.calculate_rsi(prices, 14)
    assert rsi > 70.0 # Overbought in strong uptrend

    # Strong downtrend prices
    prices_down = [200 - i * 2 for i in range(30)]
    rsi_down = TechnicalAnalysisService.calculate_rsi(prices_down, 14)
    assert rsi_down < 30.0 # Oversold in strong downtrend

def test_macd_calculation():
    prices = [100 + i * 1.5 for i in range(50)]
    macd = TechnicalAnalysisService.calculate_macd(prices)
    assert hasattr(macd, "value")
    assert hasattr(macd, "signal")
    assert hasattr(macd, "histogram")

def test_atr_and_adx_calculations():
    candles = [
        {"open": 100 + i, "high": 105 + i, "low": 98 + i, "close": 102 + i, "volume": 1000 + i * 10}
        for i in range(40)
    ]
    atr = TechnicalAnalysisService.calculate_atr(candles, 14)
    adx = TechnicalAnalysisService.calculate_adx(candles, 14)

    assert atr > 0
    assert adx >= 0 and adx <= 100

def test_bollinger_bands():
    prices = [100.0 + (i % 5) for i in range(30)]
    bb = TechnicalAnalysisService.calculate_bollinger_bands(prices, 20)
    assert bb.upper > bb.middle
    assert bb.middle > bb.lower

def test_volume_metrics():
    candles = [
        {"open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000}
        for _ in range(25)
    ]
    # Add a massive volume spike on the latest candle
    candles[-1]["volume"] = 3500
    candles[-1]["close"] = 110 # Bullish breakout bar

    vol = TechnicalAnalysisService.calculate_volume_metrics(candles)
    assert vol.is_volume_confirmed == True
    assert vol.spike_ratio >= 2.0
    assert vol.trend == "INCREASING"
