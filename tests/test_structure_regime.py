import pytest
from app.services.technical_analysis import TechnicalAnalysisService

def test_market_structure_bullish_progression():
    # Sequence of Higher Highs and Higher Lows
    candles = [
        {"open": 100, "high": 105, "low": 98, "close": 104, "volume": 1000},
        {"open": 104, "high": 102, "low": 101, "close": 102, "volume": 800},
        {"open": 102, "high": 112, "low": 100, "close": 110, "volume": 1200},
        {"open": 110, "high": 108, "low": 105, "close": 106, "volume": 900},
        {"open": 106, "high": 120, "low": 104, "close": 118, "volume": 1500},
    ]
    structure = TechnicalAnalysisService.detect_market_structure(candles)
    assert structure is not None
    assert hasattr(structure, "structure_bias")
    assert hasattr(structure, "pattern")

def test_sr_headroom_buffer_validation():
    current_price = 2650.0
    atr = 10.0
    supports = [2630.0, 2610.0]
    resistances = [2652.0, 2680.0] # Resistance only $2 above entry (< 1.5 * ATR)

    # Bullish entry right under ceiling resistance
    sr_buf_tight = TechnicalAnalysisService.validate_sr_buffer(
        current_price=current_price,
        trend="bullish",
        supports=supports,
        resistances=resistances,
        atr=atr
    )
    assert sr_buf_tight.has_sufficient_headroom == False
    assert "Insufficient headroom" in sr_buf_tight.verdict

    # Clear headroom test
    clear_resistances = [2680.0, 2700.0]
    sr_buf_clear = TechnicalAnalysisService.validate_sr_buffer(
        current_price=current_price,
        trend="bullish",
        supports=supports,
        resistances=clear_resistances,
        atr=atr
    )
    assert sr_buf_clear.has_sufficient_headroom == True
