from app.services.ai_council import AIAgentAnalystCouncil
from app.schemas.schemas import AnalystVote, TechnicalAnalysisResult, MACDResult, BollingerBandsResult
import datetime

def test_risk_analyst_veto():
    # Setup technical with high volatility and extreme RSI
    tech = TechnicalAnalysisResult(
        symbol="BTCUSDT",
        timeframe="1h",
        trend="bullish",
        momentum="strong",
        rsi=88.0, # Extreme overbought
        macd=MACDResult(value=10, signal=5, histogram=5),
        ema_20=65000, ema_50=64000, ema_200=60000,
        atr=3500.0, # Huge ATR
        bollinger_bands=BollingerBandsResult(upper=70000, middle=65000, lower=60000),
        support_levels=[62000],
        resistance_levels=[69000],
        summary="Extreme volatility",
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    risk_vote = AIAgentAnalystCouncil.evaluate_risk("BTCUSDT", 68000.0, tech, "Low")
    assert risk_vote.veto is True

    votes = {
        "technical": AnalystVote(analyst="technical", bias="bullish", confidence=80.0, reasoning="Bullish", key_levels=[]),
        "macro": AnalystVote(analyst="macro", bias="bullish", confidence=75.0, reasoning="Bullish", key_levels=[]),
        "sentiment": AnalystVote(analyst="sentiment", bias="bullish", confidence=70.0, reasoning="Bullish", key_levels=[]),
        "risk": risk_vote
    }

    consensus = AIAgentAnalystCouncil.synthesize_consensus("BTCUSDT", "1h", 68000.0, tech, votes, "Low")
    assert consensus.decision == "NO_TRADE"
    assert consensus.vetoed_by_risk is True
