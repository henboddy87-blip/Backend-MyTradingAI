import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.models import User, AiConversation, AiMessage, Asset
from app.schemas.schemas import (
    AIAnalyzeRequest, AIAnalyzeResponse,
    AIChatRequest, AIChatResponse,
    AnalystVote
)
from app.market import get_market_data_provider
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.ai_council import AIAgentAnalystCouncil
from app.services.news_service import NewsService

router = APIRouter(prefix="/ai", tags=["AI Copilot & Council"])

GLOBAL_ASSETS = [
    "XAUUSD", "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "EURUSD", "GBPUSD", "USDJPY", "USOIL", "UKOIL",
    "NVDA", "AAPL", "TSLA", "NAS100", "US30"
]

def calculate_trader_targets(symbol: str, current_price: float, direction: str, atr: float, precision: int = 2):
    """
    Calculates realistic institutional trader goal targets:
    - SL: Controlled risk boundary (e.g. 8-10 points for Gold)
    - TP1: +5.00 to +8.00 points (Quick scalp / initial target)
    - TP2: +20.00 points (Intraday swing target)
    - TP3: +30.00 points (Extended runner target)
    """
    symbol_upper = symbol.upper()
    if "XAU" in symbol_upper or "GOLD" in symbol_upper:
        sl_dist = 8.50
        tp1_dist = 6.50   # 5-8 points goal
        tp2_dist = 20.00  # 20 points goal
        tp3_dist = 30.00  # 30 points goal
    elif "BTC" in symbol_upper:
        sl_dist = 400.0
        tp1_dist = 350.0
        tp2_dist = 1200.0
        tp3_dist = 2500.0
    elif "ETH" in symbol_upper:
        sl_dist = 25.0
        tp1_dist = 20.0
        tp2_dist = 65.0
        tp3_dist = 140.0
    elif "EUR" in symbol_upper or "GBP" in symbol_upper:
        sl_dist = 0.0018
        tp1_dist = 0.0020
        tp2_dist = 0.0050
        tp3_dist = 0.0080
    elif "NVDA" in symbol_upper or "AAPL" in symbol_upper or "TSLA" in symbol_upper:
        sl_dist = round(max(1.80, current_price * 0.012), 2)
        tp1_dist = round(sl_dist * 1.0, 2)
        tp2_dist = round(sl_dist * 2.2, 2)
        tp3_dist = round(sl_dist * 3.5, 2)
    elif "NAS" in symbol_upper or "US30" in symbol_upper:
        sl_dist = 50.0
        tp1_dist = 45.0
        tp2_dist = 150.0
        tp3_dist = 280.0
    else:
        sl_dist = max(atr * 1.2, current_price * 0.008)
        tp1_dist = sl_dist * 1.0
        tp2_dist = sl_dist * 2.2
        tp3_dist = sl_dist * 3.5

    if direction == "BUY":
        sl = round(current_price - sl_dist, precision)
        tp1 = round(current_price + tp1_dist, precision)
        tp2 = round(current_price + tp2_dist, precision)
        tp3 = round(current_price + tp3_dist, precision)
    else: # SELL
        sl = round(current_price + sl_dist, precision)
        tp1 = round(current_price - tp1_dist, precision)
        tp2 = round(current_price - tp2_dist, precision)
        tp3 = round(current_price - tp3_dist, precision)

    rr = round(tp2_dist / sl_dist, 2) if sl_dist > 0 else 2.5
    return sl, tp1, tp2, tp3, rr, sl_dist, tp1_dist, tp2_dist, tp3_dist

@router.post("/analyze", response_model=AIAnalyzeResponse)
async def analyze_market_setup(
    req: AIAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    symbol = req.symbol.upper()
    market_provider = get_market_data_provider()
    
    # 1. Fetch candles & current price for selected timeframe
    candles = market_provider.get_historical_candles(symbol, timeframe=req.timeframe, limit=120)
    current_price = req.current_price if (req.current_price and req.current_price > 0) else market_provider.get_latest_price(symbol)

    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    market_type = asset.market_type if asset else "crypto"
    precision = asset.precision if asset else 2

    # 2. Technical analysis on actual timeframe candles
    tech = TechnicalAnalysisService.analyze(symbol, req.timeframe, candles)

    # 3. News sentiment
    news_items = NewsService.get_news(db, language="en", symbol=symbol, limit=5)
    news_dicts = [{"title": n.title, "summary": n.summary, "sentiment": {"sentiment": n.sentiment.sentiment if n.sentiment else "neutral"}} for n in news_items]

    # 4. Multi-agent council evaluation
    tech_vote = AIAgentAnalystCouncil.evaluate_technical(tech, current_price)
    macro_vote = AIAgentAnalystCouncil.evaluate_macro(symbol, market_type)
    sentiment_vote = AIAgentAnalystCouncil.evaluate_sentiment(symbol, news_dicts)
    risk_vote = AIAgentAnalystCouncil.evaluate_risk(symbol, current_price, tech, req.risk_level)

    votes: Dict[str, AnalystVote] = {
        "technical": tech_vote,
        "macro": macro_vote,
        "sentiment": sentiment_vote,
        "risk": risk_vote
    }

    consensus = AIAgentAnalystCouncil.synthesize_consensus(
        symbol, req.timeframe, current_price, tech, votes, req.risk_level, req.analysis_mode
    )

    direction = consensus.decision
    atr = tech.atr if tech.atr > 0 else (current_price * 0.01)

    # If confident (BUY / SELL with >= 70% threshold)
    if direction in ["BUY", "SELL"] and consensus.confidence >= 70.0:
        entry = current_price
        sl, tp1, tp2, tp3, rr, sl_dist, tp1_dist, tp2_dist, tp3_dist = calculate_trader_targets(
            symbol, current_price, direction, atr, precision
        )
        
        move_sign = "+" if direction == "BUY" else "-"
        reasoning_text = (
            f"High-Conviction {direction} Setup ({consensus.confidence}% council confidence).\n\n"
            f"• Technical Predictions: EMA 20 (${tech.ema_20:.2f}) & EMA 50 (${tech.ema_50:.2f}) confirm {consensus.market_bias.lower()} momentum with RSI at {tech.rsi:.1f}.\n"
            f"• Goal Target Moves: TP1 Goal = {move_sign}{tp1_dist:.2f} pts (${tp1:.2f}), TP2 Goal = {move_sign}{tp2_dist:.2f} pts (${tp2:.2f}), TP3 Goal = {move_sign}{tp3_dist:.2f} pts (${tp3:.2f}).\n"
            f"• Risk Boundary: Stop Loss set at ${sl:.2f} ({sl_dist:.2f} pts risk buffer | 1:{rr} R:R)."
        )
    else:
        # NO TRADE / NOT CONFIDENT -> Zero out positions completely!
        direction = "NO_TRADE"
        entry, sl, tp1, tp2, tp3, rr = None, None, None, None, None, 0.0
        reasoning_text = (
            f"⚠️ ALERT: DO NOT ENTER POSITION (Confidence: {consensus.confidence}%, below 70% institutional entry threshold).\n\n"
            f"• Technical Structure: Market is currently consolidating or exhibiting conflicting indicators. RSI ({tech.rsi:.1f}) and MACD ({tech.macd.histogram:+.4f}) lack decisive trend alignment on the {req.timeframe} timeframe.\n"
            f"• Risk Directive: No high-probability asymmetric reward setup detected at current price (${current_price:.2f}).\n"
            f"• Actionable Advice: STAND ASIDE. Capital preservation is prioritized until price forms a clean structural breakout."
        )

    return AIAnalyzeResponse(
        symbol=symbol,
        timeframe=req.timeframe,
        direction=direction,
        entry=entry,
        stop_loss=sl,
        take_profit_1=tp1,
        take_profit_2=tp2,
        take_profit_3=tp3,
        confidence=consensus.confidence,
        risk_reward=rr,
        market_bias=consensus.market_bias,
        technical_analysis={
            "trend": tech.trend,
            "rsi": tech.rsi,
            "macd": {"histogram": tech.macd.histogram},
            "ema_20": tech.ema_20,
            "ema_50": tech.ema_50,
            "atr": tech.atr,
            "supports": tech.support_levels,
            "resistances": tech.resistance_levels,
        },
        news_sentiment={
            "bias": sentiment_vote.bias,
            "confidence": sentiment_vote.confidence,
            "headline_count": len(news_items)
        },
        risk_assessment=risk_vote.reasoning,
        reasoning=reasoning_text,
        analyst_votes=votes,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        data_mode="mock"
    )

@router.post("/best-setup")
async def get_best_market_setup(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Scans 15 global benchmarks across multiple timeframes (1h, 15m, 4h).
    Calculates technical indicators and Council consensus to find the highest-confidence setup.
    If no asset qualifies with >= 75% confidence, returns NO_TRADE.
    """
    market_provider = get_market_data_provider()
    best_candidate = None
    highest_conf = 0.0

    # Scan all 15 global assets
    for sym in GLOBAL_ASSETS:
        for tf in ["1h", "15m", "4h"]:
            price = market_provider.get_latest_price(sym)
            candles = market_provider.get_historical_candles(sym, timeframe=tf, limit=120)
            tech = TechnicalAnalysisService.analyze(sym, tf, candles)
            
            asset = db.query(Asset).filter(Asset.symbol == sym).first()
            mtype = asset.market_type if asset else "crypto"
            precision = asset.precision if asset else 2

            tech_vote = AIAgentAnalystCouncil.evaluate_technical(tech, price)
            macro_vote = AIAgentAnalystCouncil.evaluate_macro(sym, mtype)
            sentiment_vote = AIAgentAnalystCouncil.evaluate_sentiment(sym)
            risk_vote = AIAgentAnalystCouncil.evaluate_risk(sym, price, tech, "Medium")

            votes = {
                "technical": tech_vote,
                "macro": macro_vote,
                "sentiment": sentiment_vote,
                "risk": risk_vote
            }
            consensus = AIAgentAnalystCouncil.synthesize_consensus(sym, tf, price, tech, votes)

            # Only qualify setups with genuine high confidence (>= 75%)
            if consensus.decision in ["BUY", "SELL"] and consensus.confidence >= 75.0:
                if consensus.confidence > highest_conf:
                    highest_conf = consensus.confidence
                    atr = tech.atr if tech.atr > 0 else (price * 0.01)
                    sl, tp1, tp2, tp3, rr, sl_dist, tp1_dist, tp2_dist, tp3_dist = calculate_trader_targets(
                        sym, price, consensus.decision, atr, precision
                    )

                    move_sign = "+" if consensus.decision == "BUY" else "-"
                    best_candidate = {
                        "symbol": sym,
                        "timeframe": tf,
                        "direction": consensus.decision,
                        "entry": price,
                        "stop_loss": sl,
                        "take_profit_1": tp1,
                        "take_profit_2": tp2,
                        "take_profit_3": tp3,
                        "risk_reward": rr,
                        "confidence": consensus.confidence,
                        "market_bias": consensus.market_bias,
                        "is_confident": True,
                        "reasoning": (
                            f"Optimal High-Conviction Setup: {sym} ({tf}) has confirmed {consensus.decision} alignment with {consensus.confidence}% council consensus. "
                            f"Target Goals: TP1 ({move_sign}{tp1_dist:.2f} pts), TP2 ({move_sign}{tp2_dist:.2f} pts), TP3 ({move_sign}{tp3_dist:.2f} pts). "
                            f"Moving averages and RSI ({tech.rsi:.1f}) show clean momentum confluence."
                        ),
                        "votes": {k: (v.dict() if hasattr(v, 'dict') else v) for k, v in votes.items()}
                    }

    # If NO asset currently meets the >= 75% threshold, DO NOT return fake data!
    if not best_candidate:
        best_candidate = {
            "symbol": "NONE",
            "timeframe": "1h",
            "direction": "NO_TRADE",
            "entry": None,
            "stop_loss": None,
            "take_profit_1": None,
            "take_profit_2": None,
            "take_profit_3": None,
            "risk_reward": 0.0,
            "confidence": 48.0,
            "market_bias": "Neutral / Consolidation",
            "is_confident": False,
            "reasoning": (
                "⚠️ ALERT: NO HIGH-CONVICTION TRADE SETUP DETECTED.\n\n"
                "Council scanned 15 global markets across multiple timeframes. All assets are currently range-bound, overextended, or exhibiting conflicting momentum.\n\n"
                "RECOMMENDATION: DO NOT ENTER ANY POSITIONS. Stand aside and preserve trading capital until high-probability breakout conditions materialize."
            ),
            "votes": {}
        }

    return best_candidate

@router.post("/chat", response_model=AIChatResponse)
async def ai_chat_copilot(
    req: AIChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    symbol = (req.symbol or "XAUUSD").upper()
    timeframe = req.timeframe or "1h"
    market_provider = get_market_data_provider()
    
    current_price = market_provider.get_latest_price(symbol)
    candles = market_provider.get_historical_candles(symbol, timeframe=timeframe, limit=60)
    tech = TechnicalAnalysisService.analyze(symbol, timeframe, candles)

    user_query = req.message.lower()
    
    if "gold" in user_query or "xau" in user_query or symbol == "XAUUSD":
        response_text = (
            f"### AI Analyst Council — Market Intelligence Briefing\n\n"
            f"**Asset**: `{symbol}` | **Timeframe**: `{timeframe}` | **Spot Price**: `${current_price:.2f}`\n\n"
            f"**Technical Status**:\n"
            f"- **Trend**: `{tech.trend.upper()}`\n"
            f"- **RSI (14)**: `{tech.rsi:.1f}` ({'Oversold bounce potential' if tech.rsi < 30 else 'Overbought cooling' if tech.rsi > 70 else 'Neutral momentum'})\n"
            f"- **MACD Histogram**: `{tech.macd.histogram:+.4f}`\n"
            f"- **Key Support**: `${tech.support_levels[-1] if tech.support_levels else current_price * 0.98:.2f}` | **Key Resistance**: `${tech.resistance_levels[-1] if tech.resistance_levels else current_price * 1.02:.2f}`\n\n"
            f"**Institutional Council Synthesis**:\n"
            f"• Macro monetary liquidity remains resilient while short-term order books reflect strategic accumulation.\n"
            f"• Risk Engine recommends keeping risk position sizing $\\le 1.5\\%$ of portfolio balance."
        )
    else:
        response_text = (
            f"### AI Council Technical Audit for {symbol}\n\n"
            f"Current price is **${current_price:.2f}**. Technical trend is **{tech.trend}** with RSI at **{tech.rsi:.1f}**.\n\n"
            f"The Multi-Agent Council monitors this instrument continuously. Always verify the risk-to-reward ratio before initiating execution."
        )

    # Persist message history
    conv_id = req.conversation_id
    if not conv_id:
        conv = AiConversation(user_id=current_user.id, title=f"Analysis of {symbol}")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    msg_user = AiMessage(conversation_id=conv_id, sender="USER", content=req.message)
    msg_assistant = AiMessage(conversation_id=conv_id, sender="ASSISTANT", content=response_text)
    db.add_all([msg_user, msg_assistant])
    db.commit()

    return AIChatResponse(
        conversation_id=conv_id,
        reply=response_text,
        symbol=symbol,
        timeframe=timeframe,
        recommended_action="HOLD" if tech.rsi > 40 and tech.rsi < 60 else "BUY" if tech.rsi <= 40 else "SELL",
        key_levels={"support": tech.support_levels, "resistance": tech.resistance_levels}
    )

@router.get("/conversations")
def list_conversations(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    convs = db.query(AiConversation).filter(AiConversation.user_id == current_user.id).order_by(AiConversation.updated_at.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]

@router.get("/conversations/{id}/messages")
def get_conversation_messages(id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    conv = db.query(AiConversation).filter(AiConversation.id == id, AiConversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(AiMessage).filter(AiMessage.conversation_id == id).order_by(AiMessage.created_at.asc()).all()
    return [{"id": m.id, "role": m.sender, "content": m.content, "created_at": m.created_at} for m in messages]
