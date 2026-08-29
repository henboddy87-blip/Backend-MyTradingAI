import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Signal, SignalOutcome, Asset
from app.market import get_market_data_provider
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.ai_council import AIAgentAnalystCouncil
from app.services.risk_engine import RiskEngine
from app.core.logging import logger

class SignalEngine:
    @classmethod
    def generate_signal(
        cls,
        db: Session,
        symbol: str,
        timeframe: str = "1h",
        risk_level: str = "Medium",
        analysis_mode: str = "Intraday",
        is_pro_only: bool = False
    ) -> Signal:
        symbol = symbol.upper()
        market_provider = get_market_data_provider()
        
        # 1. WAKE: Get candles and current market price
        candles = market_provider.get_historical_candles(symbol, timeframe=timeframe, limit=120)
        current_price = market_provider.get_latest_price(symbol)
        
        # Get asset metadata
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        market_type = asset.market_type if asset else "crypto"
        precision = asset.precision if asset else 2

        # 2. SCAN: Calculate technical indicators
        tech = TechnicalAnalysisService.analyze(symbol, timeframe, candles)

        # 3. DEBATE: Multi-Agent Council
        tech_vote = AIAgentAnalystCouncil.evaluate_technical(tech, current_price)
        macro_vote = AIAgentAnalystCouncil.evaluate_macro(symbol, market_type)
        sentiment_vote = AIAgentAnalystCouncil.evaluate_sentiment(symbol)
        risk_vote = AIAgentAnalystCouncil.evaluate_risk(symbol, current_price, tech, risk_level)

        votes = {
            "technical": tech_vote,
            "macro": macro_vote,
            "sentiment": sentiment_vote,
            "risk": risk_vote
        }

        consensus = AIAgentAnalystCouncil.synthesize_consensus(
            symbol, timeframe, current_price, tech, votes, risk_level, analysis_mode
        )

        direction = consensus.decision
        atr = tech.atr if tech.atr > 0 else (current_price * 0.01)

        # 4. VALIDATE & CALCULATE ENTRY / SL / TP
        if direction in ["BUY", "SELL"] and consensus.confidence >= 70.0:
            entry = current_price
            from app.api.routes.ai import calculate_trader_targets
            stop_loss, tp1, tp2, tp3, risk_reward, sl_dist, tp1_dist, tp2_dist, tp3_dist = calculate_trader_targets(
                symbol, current_price, direction, atr, precision
            )
        else: # NO_TRADE
            entry = None
            stop_loss = None
            tp1 = None
            tp2 = None
            tp3 = None
            risk_reward = 0.0

        # Save to database
        now = datetime.datetime.utcnow()
        signal = Signal(
            symbol=symbol,
            market_type=market_type,
            timeframe=timeframe,
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            confidence=consensus.confidence,
            risk_reward=risk_reward,
            bias=consensus.market_bias,
            technical_summary=tech.summary,
            sentiment_summary=sentiment_vote.reasoning,
            risk_assessment=risk_vote.reasoning,
            reasoning=consensus.reasons[0] if consensus.reasons else "Market council assessment completed.",
            analyst_votes_json={k: v.dict() for k, v in votes.items()},
            status="ACTIVE" if direction != "NO_TRADE" else "NO_TRADE",
            is_pro_only=is_pro_only,
            created_at=now,
            published_at=now
        )

        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal

    @classmethod
    def evaluate_active_signals(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Background lifecycle evaluator: Checks active signals against current live prices
        Updates status to TP1_HIT, TP2_HIT, TP3_HIT, SL_HIT, or EXPIRED.
        """
        active_signals = db.query(Signal).filter(Signal.status.in_(["ACTIVE", "TP1_HIT", "TP2_HIT"])).all()
        market_provider = get_market_data_provider()
        updates = []
        now = datetime.datetime.utcnow()

        for sig in active_signals:
            current_price = market_provider.get_latest_price(sig.symbol)
            changed = False
            outcome = None
            pnl_r = 0.0

            if sig.direction == "BUY":
                if current_price <= sig.stop_loss:
                    sig.status = "SL_HIT"
                    sig.closed_at = now
                    sig.exit_price = sig.stop_loss
                    sig.pnl_r = -1.0
                    sig.pnl_percentage = round(((sig.stop_loss - sig.entry) / sig.entry) * 100.0, 2)
                    outcome = "LOSS"
                    changed = True
                elif current_price >= sig.take_profit_3:
                    sig.status = "TP3_HIT"
                    sig.closed_at = now
                    sig.exit_price = sig.take_profit_3
                    sig.pnl_r = 3.5
                    sig.pnl_percentage = round(((sig.take_profit_3 - sig.entry) / sig.entry) * 100.0, 2)
                    outcome = "WIN"
                    changed = True
                elif current_price >= sig.take_profit_2 and sig.status != "TP2_HIT":
                    sig.status = "TP2_HIT"
                    changed = True
                elif current_price >= sig.take_profit_1 and sig.status != "TP1_HIT":
                    sig.status = "TP1_HIT"
                    changed = True
                    
            elif sig.direction == "SELL":
                if current_price >= sig.stop_loss:
                    sig.status = "SL_HIT"
                    sig.closed_at = now
                    sig.exit_price = sig.stop_loss
                    sig.pnl_r = -1.0
                    sig.pnl_percentage = round(((sig.entry - sig.stop_loss) / sig.entry) * 100.0, 2)
                    outcome = "LOSS"
                    changed = True
                elif current_price <= sig.take_profit_3:
                    sig.status = "TP3_HIT"
                    sig.closed_at = now
                    sig.exit_price = sig.take_profit_3
                    sig.pnl_r = 3.5
                    sig.pnl_percentage = round(((sig.entry - sig.take_profit_3) / sig.entry) * 100.0, 2)
                    outcome = "WIN"
                    changed = True
                elif current_price <= sig.take_profit_2 and sig.status != "TP2_HIT":
                    sig.status = "TP2_HIT"
                    changed = True
                elif current_price <= sig.take_profit_1 and sig.status != "TP1_HIT":
                    sig.status = "TP1_HIT"
                    changed = True

            # Check expiration after 48 hours
            if not changed and (now - sig.created_at).total_seconds() > 172800:
                sig.status = "EXPIRED"
                sig.closed_at = now
                sig.exit_price = current_price
                outcome = "EXPIRED"
                changed = True

            if changed:
                if outcome:
                    dur_min = int((now - sig.created_at).total_seconds() / 60)
                    sig_outcome = SignalOutcome(
                        signal_id=sig.id,
                        symbol=sig.symbol,
                        outcome=outcome,
                        pnl_r=sig.pnl_r,
                        pnl_pct=sig.pnl_percentage,
                        duration_minutes=dur_min,
                        recorded_at=now
                    )
                    db.add(sig_outcome)
                
                updates.append({"id": sig.id, "symbol": sig.symbol, "status": sig.status})

        if updates:
            db.commit()
            logger.info(f"Signal lifecycle evaluation updated {len(updates)} signals.")

        return updates

    @classmethod
    def auto_scan_and_generate_signals(cls, db: Session, target_count: int = 5) -> List[Signal]:
        """
        Autonomous market scanner: Scans all benchmarks and timeframes.
        Generates and publishes verified signals based on real strategy and council debate.
        """
        symbols = [
            "XAUUSD", "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
            "EURUSD", "GBPUSD", "USDJPY", "USOIL", "UKOIL",
            "NVDA", "AAPL", "TSLA", "NAS100", "US30"
        ]
        timeframes = ["15m", "1h", "4h", "1d"]
        generated = []

        for sym in symbols:
            if len(generated) >= target_count:
                break
            for tf in timeframes:
                if len(generated) >= target_count:
                    break
                try:
                    sig = cls.generate_signal(db, symbol=sym, timeframe=tf, risk_level="Medium", is_pro_only=False)
                    if sig.direction != "NO_TRADE":
                        generated.append(sig)
                except Exception as e:
                    logger.error(f"Error auto-scanning {sym} ({tf}): {e}")

        logger.info(f"Auto-scan generated {len(generated)} verified market signals.")
        return generated
