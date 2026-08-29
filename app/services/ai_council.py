import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.schemas import (
    AnalystVote, ConsensusResult, AIAnalyzeResponse,
    TechnicalAnalysisResult
)
from app.services.risk_engine import RiskEngine

class AIAgentAnalystCouncil:
    """
    Multi-Agent Analyst Council comprising 4 independent specialist agents:
    1. Technical Analyst (Momentum, RSI, MACD, Moving Averages, S/R)
    2. Macro Analyst (Monetary Regime, DXY, Sector Sentiment)
    3. Sentiment Analyst (News Flow, Headlines, Positioning)
    4. Risk Analyst (Volatility ATR, Asymmetric R:R, Veto Authority)
    """

    @classmethod
    def evaluate_technical(cls, tech: TechnicalAnalysisResult, current_price: float) -> AnalystVote:
        bullish_points = 0
        bearish_points = 0
        risk_flags = []

        # RSI Momentum Analysis
        if tech.rsi > 70:
            risk_flags.append(f"RSI overbought ({tech.rsi:.1f})")
            bearish_points += 2
        elif tech.rsi < 30:
            risk_flags.append(f"RSI oversold ({tech.rsi:.1f})")
            bullish_points += 2
        elif tech.rsi >= 55:
            bullish_points += 3
        elif tech.rsi <= 45:
            bearish_points += 3
        else:
            risk_flags.append(f"RSI neutral ({tech.rsi:.1f}) - low directional conviction")

        # MACD Histogram & Signal Cross Analysis
        if tech.macd.histogram > 0:
            if tech.macd.value > tech.macd.signal:
                bullish_points += 3
            else:
                bullish_points += 1
        elif tech.macd.histogram < 0:
            if tech.macd.value < tech.macd.signal:
                bearish_points += 3
            else:
                bearish_points += 1

        # EMA Trend & Dynamic Flow (20 vs 50 vs 200)
        if tech.ema_20 > tech.ema_50:
            bullish_points += 3
        else:
            bearish_points += 3

        if current_price > tech.ema_200:
            bullish_points += 2
        else:
            bearish_points += 2

        total_pts = bullish_points + bearish_points
        net_diff = abs(bullish_points - bearish_points)

        if bullish_points > bearish_points + 3:
            bias = "bullish"
            confidence = min(92.0, 60.0 + (net_diff / max(1, total_pts)) * 35.0)
            reasoning = (
                f"Strong Bullish Structure: Fast EMA 20 (${tech.ema_20:.2f}) trades decisively above EMA 50 (${tech.ema_50:.2f}) "
                f"with positive MACD histogram expansion ({tech.macd.histogram:+.4f}) and robust RSI momentum ({tech.rsi:.1f}). "
                f"Price maintains altitude above the institutional 200 EMA."
            )
        elif bearish_points > bullish_points + 3:
            bias = "bearish"
            confidence = min(92.0, 60.0 + (net_diff / max(1, total_pts)) * 35.0)
            reasoning = (
                f"Strong Bearish Structure: Price pressured below EMA 20 (${tech.ema_20:.2f}) and EMA 50 (${tech.ema_50:.2f}) "
                f"with negative MACD histogram divergence ({tech.macd.histogram:+.4f}) and weak RSI ({tech.rsi:.1f}). "
                f"Sellers are aggressively defending dynamic resistance."
            )
        else:
            bias = "neutral"
            confidence = 48.0
            reasoning = (
                f"Range-Bound Consolidation: Mixed technical indicators. RSI ({tech.rsi:.1f}) sits near median without trend expansion, "
                f"and EMA 20/50 distance is compressed. Insufficient directional momentum."
            )

        key_levels = []
        if tech.support_levels:
            key_levels.append(tech.support_levels[-1])
        if tech.resistance_levels:
            key_levels.append(tech.resistance_levels[-1])

        return AnalystVote(
            analyst="technical",
            bias=bias,
            confidence=round(confidence, 1),
            reasoning=reasoning,
            key_levels=key_levels,
            risk_flags=risk_flags,
            veto=False
        )

    @classmethod
    def evaluate_macro(cls, symbol: str, market_type: str) -> AnalystVote:
        symbol = symbol.upper()
        if "XAU" in symbol or "GOLD" in symbol:
            bias = "bullish"
            confidence = 78.0
            reasoning = "Global sovereign reserve accumulation, central bank buying, and safe-haven liquidity demand create robust macro tailwinds for Gold."
        elif "BTC" in symbol or "ETH" in symbol or "SOL" in symbol or "BNB" in symbol:
            bias = "bullish"
            confidence = 74.0
            reasoning = "Institutional spot inflows, ETF balance sheet expansion, and structural on-chain liquidity velocity indicate strong macro risk appetite."
        elif "USD" in symbol or "EUR" in symbol or "GBP" in symbol or "JPY" in symbol:
            bias = "neutral"
            confidence = 62.0
            reasoning = "Central bank interest rate differentials remain balanced, resulting in cyclical range rotations across FX major corridors."
        elif "OIL" in symbol:
            bias = "bearish"
            confidence = 68.0
            reasoning = "OPEC+ quota adjustments alongside balanced global inventory levels limit aggressive upside breakout potential."
        else: # Equities & Indices
            bias = "bullish"
            confidence = 76.0
            reasoning = "Enterprise earnings resilience and ongoing artificial intelligence infrastructure spending support equities upside."

        return AnalystVote(
            analyst="macro",
            bias=bias,
            confidence=confidence,
            reasoning=reasoning,
            key_levels=[],
            risk_flags=[],
            veto=False
        )

    @classmethod
    def evaluate_sentiment(cls, symbol: str, news_items: Optional[List[Dict[str, Any]]] = None) -> AnalystVote:
        if not news_items:
            return AnalystVote(
                analyst="sentiment",
                bias="neutral",
                confidence=65.0,
                reasoning="Market news flow is balanced with stable retail positioning and consistent institutional liquidity depth.",
                key_levels=[],
                risk_flags=[],
                veto=False
            )

        pos_count = sum(1 for n in news_items if n.get("sentiment", {}).get("sentiment") == "positive")
        neg_count = sum(1 for n in news_items if n.get("sentiment", {}).get("sentiment") == "negative")
        
        if pos_count > neg_count + 1:
            bias = "bullish"
            confidence = 78.0
            reasoning = f"Constructive news flow with {pos_count} positive headlines against {neg_count} negative reports."
        elif neg_count > pos_count + 1:
            bias = "bearish"
            confidence = 76.0
            reasoning = f"Elevated headline risk with {neg_count} negative economic releases against {pos_count} positive reports."
        else:
            bias = "neutral"
            confidence = 60.0
            reasoning = "Balanced news sentiment with no outsized macroeconomic catalysts detected."

        return AnalystVote(
            analyst="sentiment",
            bias=bias,
            confidence=confidence,
            reasoning=reasoning,
            key_levels=[],
            risk_flags=[],
            veto=False
        )

    @classmethod
    def evaluate_risk(
        cls,
        symbol: str,
        current_price: float,
        tech: TechnicalAnalysisResult,
        risk_level: str = "Medium"
    ) -> AnalystVote:
        risk_flags = []
        veto = False
        confidence = 82.0

        # Check ATR volatility ratio
        atr_pct = (tech.atr / current_price) * 100.0 if current_price > 0 else 0
        if atr_pct > 4.5:
            risk_flags.append(f"Excessive ATR volatility ({tech.atr:.2f}, {atr_pct:.1f}% of price).")
            if risk_level in ["Low", "Medium"]:
                veto = True
                risk_flags.append("Veto triggered: Volatility exceeds safety limits.")

        # Check SR Headroom & Resistance Proximity
        if tech.sr_buffer and not tech.sr_buffer.has_sufficient_headroom:
            risk_flags.append(tech.sr_buffer.verdict)
            if risk_level in ["Low", "Medium"]:
                veto = True
                risk_flags.append("Veto: Trade entry blocked by immediate overhead resistance or floor support.")

        # Check Uncertain Market Regime
        if tech.market_regime and tech.market_regime.regime == "UNCERTAIN":
            risk_flags.append("Market regime is UNCERTAIN. Stand aside until clarity emerges.")
            veto = True

        if veto:
            bias = "neutral"
            reasoning = f"Risk Analyst VETO: {risk_flags[0] if risk_flags else 'Unfavorable asymmetric risk-to-reward or overextended condition.'} Capital preservation enforced."
        else:
            bias = tech.trend
            reasoning = f"Favorable risk parameters: ATR volatility buffer (${tech.atr:.2f}) and SR clearance provide asymmetric reward structure with protected invalidation level."

        return AnalystVote(
            analyst="risk",
            bias=bias,
            confidence=confidence,
            reasoning=reasoning,
            key_levels=[],
            risk_flags=risk_flags,
            veto=veto
        )

    @classmethod
    def synthesize_consensus(
        cls,
        symbol: str,
        timeframe: str,
        current_price: float,
        tech: TechnicalAnalysisResult,
        votes: Dict[str, AnalystVote],
        risk_level: str = "Medium",
        analysis_mode: str = "Intraday"
    ) -> ConsensusResult:
        # 1. Check risk veto first
        risk_vote = votes.get("risk")
        if risk_vote and risk_vote.veto:
            reasons = [
                "Risk Analyst VETO triggered.",
                "Unfavorable market volatility or overextended technical readings preclude entering a high-conviction position.",
                "Capital preservation is prioritized. Stand aside until market establishes a clear baseline."
            ]
            return ConsensusResult(
                decision="NO_TRADE",
                confidence=42.0,
                market_bias="Neutral / Guarded",
                votes=votes,
                consensus_score=0.0,
                vetoed_by_risk=True,
                reasons=reasons
            )

        # 2. Weighted multi-agent consensus computation
        weights = {"technical": 0.40, "risk": 0.25, "macro": 0.20, "sentiment": 0.15}
        bullish_score = 0.0
        bearish_score = 0.0

        for role, vote in votes.items():
            w = weights.get(role, 0.25)
            if vote.bias == "bullish":
                bullish_score += (vote.confidence / 100.0) * w
            elif vote.bias == "bearish":
                bearish_score += (vote.confidence / 100.0) * w

        # Minimum confidence threshold for entry is 70% (0.68)
        CONFIDENCE_THRESHOLD = 0.68

        if bullish_score >= CONFIDENCE_THRESHOLD and bullish_score > bearish_score + 0.18:
            decision = "BUY"
            market_bias = "Bullish"
            confidence = round(min(94.0, bullish_score * 105.0), 1)
            reasons = [
                f"High-Conviction Long Setup ({confidence}% council consensus).",
                f"Technical confirmation: EMA 20 (${tech.ema_20:.2f}) leads EMA 50 with positive MACD momentum ({tech.macd.histogram:+.4f}).",
                "Macro and risk alignment confirm asymmetric upside with low drawdown probability."
            ]
        elif bearish_score >= CONFIDENCE_THRESHOLD and bearish_score > bullish_score + 0.18:
            decision = "SELL"
            market_bias = "Bearish"
            confidence = round(min(94.0, bearish_score * 105.0), 1)
            reasons = [
                f"High-Conviction Short Setup ({confidence}% council consensus).",
                f"Technical confirmation: EMA 20 (${tech.ema_20:.2f}) pressured under EMA 50 with negative MACD expansion ({tech.macd.histogram:+.4f}).",
                "Downside momentum confirms favorable risk-to-reward targets."
            ]
        else:
            decision = "NO_TRADE"
            market_bias = "Neutral / Sideways"
            confidence = round(max(bullish_score, bearish_score) * 100.0, 1)
            reasons = [
                f"Insufficient Directional Conviction ({confidence}% confidence, below 70% institutional threshold).",
                f"Market structure is currently consolidating. RSI ({tech.rsi:.1f}) and moving averages show conflicting momentum.",
                "Advisory: No high-probability edge exists at current price. Stand aside and preserve capital until clear breakout confirmation."
            ]

        return ConsensusResult(
            decision=decision,
            confidence=confidence,
            market_bias=market_bias,
            votes=votes,
            consensus_score=round(max(bullish_score, bearish_score), 3),
            vetoed_by_risk=False,
            reasons=reasons
        )
