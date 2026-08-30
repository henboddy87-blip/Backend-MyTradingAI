import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import Signal, SignalOutcome, Asset
from app.market import get_market_data_provider
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.ai_council import AIAgentAnalystCouncil
from app.services.news_service import NewsService
from app.services.risk_engine import RiskEngine
from app.core.logging import logger

class SignalEngine:
    @classmethod
    def calculate_confluence_scores(
        cls,
        tech,
        mtf,
        news_analysis,
        event_risk,
        current_price: float,
        smc: Optional[Any] = None
    ) -> Dict[str, float]:
        """
        Combines institutional evidence pillars using configurable weights from backend Settings:
        - Market Structure (20%)
        - Higher-Timeframe Trend (15%)
        - Trend Indicators (10%)
        - Momentum (10%)
        - Multi-Timeframe Alignment (15%)
        - Support/Resistance & Headroom (10%)
        - Volatility & Regime (5%)
        - Volume Confirmation (5%)
        - News & Sentiment (5%)
        - Risk/Reward Buffer (5%)
        + Smart Money Concepts (SMC) Premium/Discount & FVG/OB Confluence Multiplier
        """
        w_struct = settings.WEIGHT_MARKET_STRUCTURE
        w_htf = settings.WEIGHT_HTF_TREND
        w_trend = settings.WEIGHT_TREND_INDICATORS
        w_mom = settings.WEIGHT_MOMENTUM
        w_mtf = settings.WEIGHT_MULTI_TIMEFRAME
        w_sr = settings.WEIGHT_SUPPORT_RESISTANCE
        w_vol = settings.WEIGHT_VOLATILITY
        w_volume = settings.WEIGHT_VOLUME
        w_news = settings.WEIGHT_NEWS
        w_rr = settings.WEIGHT_RISK_REWARD

        buy_pts = 0.0
        sell_pts = 0.0

        # 1. Market Structure (20%)
        if tech.market_structure:
            if tech.market_structure.structure_bias == "BULLISH":
                buy_pts += w_struct * 100.0 * (1.1 if tech.market_structure.break_of_structure else 1.0)
            elif tech.market_structure.structure_bias == "BEARISH":
                sell_pts += w_struct * 100.0 * (1.1 if tech.market_structure.break_of_structure else 1.0)
            else:
                buy_pts += w_struct * 45.0
                sell_pts += w_struct * 45.0

        # 2. HTF Trend (15%)
        if mtf and "4h" in mtf.timeframes:
            tf4h = mtf.timeframes["4h"]
            if tf4h.trend == "BULLISH":
                buy_pts += w_htf * 100.0
            elif tf4h.trend == "BEARISH":
                sell_pts += w_htf * 100.0
            else:
                buy_pts += w_htf * 50.0
                sell_pts += w_htf * 50.0

        # 3. Trend Indicators (10%) - EMA 20, 50, 100, 200 & ADX
        if tech.ema_20 > tech.ema_50 and current_price > tech.ema_200:
            buy_pts += w_trend * 100.0
        elif tech.ema_20 < tech.ema_50 and current_price < tech.ema_200:
            sell_pts += w_trend * 100.0
        else:
            buy_pts += w_trend * 40.0
            sell_pts += w_trend * 40.0

        # 4. Momentum (10%) - RSI & MACD & Stochastics
        if tech.rsi >= 52 and tech.macd.histogram > 0:
            buy_pts += w_mom * 100.0
        elif tech.rsi <= 48 and tech.macd.histogram < 0:
            sell_pts += w_mom * 100.0
        else:
            buy_pts += w_mom * 50.0
            sell_pts += w_mom * 50.0

        # 5. Multi-Timeframe Alignment (15%)
        if mtf:
            if mtf.alignment_state == "ALIGNED_BULLISH":
                buy_pts += w_mtf * mtf.alignment_score
            elif mtf.alignment_state == "ALIGNED_BEARISH":
                sell_pts += w_mtf * mtf.alignment_score
            else:
                buy_pts += w_mtf * 40.0
                sell_pts += w_mtf * 40.0

        # 6. Support/Resistance & Headroom (10%)
        if tech.sr_buffer:
            if tech.sr_buffer.has_sufficient_headroom:
                if tech.trend == "bullish":
                    buy_pts += w_sr * 100.0
                elif tech.trend == "bearish":
                    sell_pts += w_sr * 100.0
            else:
                # Deduct points if entering directly into ceiling/floor!
                if tech.trend == "bullish":
                    buy_pts -= w_sr * 50.0
                else:
                    sell_pts -= w_sr * 50.0

        # 7. Volatility & Regime (5%)
        if tech.market_regime:
            if tech.market_regime.regime in ["STRONG_TREND", "PULLBACK"]:
                if tech.trend == "bullish":
                    buy_pts += w_vol * 100.0
                else:
                    sell_pts += w_vol * 100.0
            elif tech.market_regime.regime == "UNCERTAIN":
                buy_pts *= 0.70
                sell_pts *= 0.70

        # 8. Volume Confirmation (5%)
        if tech.volume_metrics and tech.volume_metrics.is_volume_confirmed:
            if tech.trend == "bullish":
                buy_pts += w_volume * 100.0
            else:
                sell_pts += w_volume * 100.0

        # 9. News & Sentiment (5%)
        if news_analysis and news_analysis.get("status") == "CONFIRMATION":
            if news_analysis.get("news_bias") == "BULLISH":
                buy_pts += w_news * 100.0
            else:
                sell_pts += w_news * 100.0
        elif news_analysis and news_analysis.get("status") == "CONFLICT":
            buy_pts -= w_news * 30.0
            sell_pts -= w_news * 30.0

        # 10. Risk/Reward (5%)
        buy_pts += w_rr * 90.0
        sell_pts += w_rr * 90.0

        # 11. Smart Money Concepts (SMC) Synergy Multiplier
        if smc:
            if smc.premium_discount_zone == "DISCOUNT_UNDERVALUED":
                buy_pts *= 1.10
                sell_pts *= 0.85
            elif smc.premium_discount_zone == "PREMIUM_OVERVALUED":
                sell_pts *= 1.10
                buy_pts *= 0.85

            if smc.smc_bias in ["STRONG_BULLISH", "BULLISH"]:
                buy_pts += 5.0
            elif smc.smc_bias in ["STRONG_BEARISH", "BEARISH"]:
                sell_pts += 5.0

        # 12. Phase 3: Institutional Session & Killzone Multiplier
        session_info = TechnicalAnalysisService.get_current_trading_session()
        sess_mult = session_info.get("score_multiplier", 1.0)
        buy_pts *= sess_mult
        sell_pts *= sess_mult

        # 13. Smart Money Liquidity Sweep Stop-Hunt Confluence
        if smc and getattr(smc, 'liquidity_sweeps', None):
            for sweep in smc.liquidity_sweeps[:2]:
                if sweep.reversal_bias == "BULLISH":
                    buy_pts += 4.0
                    sell_pts *= 0.92
                elif sweep.reversal_bias == "BEARISH":
                    sell_pts += 4.0
                    buy_pts *= 0.92

        # If imminent high-impact event risk is detected -> discount both sides!
        if event_risk and event_risk.get("news_risk") == "HIGH":
            buy_pts *= 0.65
            sell_pts *= 0.65

        buy_score = round(max(0.0, min(98.0, buy_pts)), 1)
        sell_score = round(max(0.0, min(98.0, sell_pts)), 1)

        return {
            "buy_score": buy_score,
            "sell_score": sell_score,
            "net_advantage": round(abs(buy_score - sell_score), 1)
        }

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
        
        # 1. Fetch candles & current market price
        candles = market_provider.get_historical_candles(symbol, timeframe=timeframe, limit=120)
        current_price = market_provider.get_latest_price(symbol)
        
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        market_type: str = str(getattr(asset, 'market_type', 'crypto')) if asset else "crypto"
        precision: int = int(getattr(asset, 'precision', 2)) if asset else 2

        # 2. Quantitative scan & Smart Money Concepts
        tech = TechnicalAnalysisService.analyze(symbol, timeframe, candles)
        smc = TechnicalAnalysisService.calculate_smart_money_concepts(candles, timeframe=timeframe, current_price=current_price)
        session_info = TechnicalAnalysisService.get_current_trading_session()

        # 3. Multi-Timeframe Alignment Matrix
        from app.api.routes.ai import compute_multi_timeframe_summary, calculate_trader_targets
        mtf = compute_multi_timeframe_summary(symbol, market_provider)

        # 4. News Sentiment & Imminent Event Risk
        news_items = NewsService.get_news(db, language="en", symbol=symbol, limit=8)
        news_sentiment = NewsService.calculate_news_sentiment_breakdown(symbol, news_items)
        event_risk = NewsService.check_economic_event_risk(symbol)
        news_confirm = NewsService.evaluate_news_technical_confirmation(
            tech.trend, news_sentiment.get("bias", "NEUTRAL"), event_risk.get("news_risk", "LOW")
        )
        news_confirm["news_bias"] = news_sentiment.get("bias", "NEUTRAL")

        # 5. Calculate Evidence-Based Confluence Scores across 10 Pillars + SMC + Session + Liquidity Sweeps
        scores = cls.calculate_confluence_scores(tech, mtf, news_confirm, event_risk, current_price, smc=smc)
        buy_score = scores["buy_score"]
        sell_score = scores["sell_score"]
        net_advantage = scores["net_advantage"]

        # 6. Multi-Agent Council
        tech_vote = AIAgentAnalystCouncil.evaluate_technical(tech, current_price)
        macro_vote = AIAgentAnalystCouncil.evaluate_macro(symbol, market_type)
        sentiment_vote = AIAgentAnalystCouncil.evaluate_sentiment(
            symbol,
            [{"title": n.title, "summary": n.summary, "sentiment": {"sentiment": n.sentiment.sentiment if n.sentiment else "neutral"}} for n in news_items]
        )
        risk_vote = AIAgentAnalystCouncil.evaluate_risk(symbol, current_price, tech, risk_level)

        votes = {
            "technical": tech_vote,
            "macro": macro_vote,
            "sentiment": sentiment_vote,
            "risk": risk_vote
        }

        # 7. Strict Decision Engine (BUY / SELL / WAIT)
        min_score = settings.SIGNAL_ENTRY_MIN_SCORE # 70.0
        min_adv = settings.SIGNAL_MIN_DIRECTIONAL_ADVANTAGE # 25.0

        if (
            buy_score >= min_score
            and buy_score > sell_score + min_adv
            and not risk_vote.veto
            and event_risk.get("news_risk") != "HIGH"
            and tech.sr_buffer
            and tech.sr_buffer.has_sufficient_headroom
        ):
            direction = "BUY"
            confidence = buy_score
            bias = "Bullish"
        elif (
            sell_score >= min_score
            and sell_score > buy_score + min_adv
            and not risk_vote.veto
            and event_risk.get("news_risk") != "HIGH"
            and tech.sr_buffer
            and tech.sr_buffer.has_sufficient_headroom
        ):
            direction = "SELL"
            confidence = sell_score
            bias = "Bearish"
        else:
            direction = "NO_TRADE"
            confidence = max(buy_score, sell_score)
            bias = "Neutral / Consolidation"

        atr = tech.atr if tech.atr > 0 else (current_price * 0.01)

        # 8. Calculate Entry, SL, TP Goals with Multi-Phase Execution Positioning
        if direction in ["BUY", "SELL"]:
            entry = current_price
            stop_loss, tp1, tp2, tp3, risk_reward, sl_dist, tp1_dist, tp2_dist, tp3_dist = calculate_trader_targets(
                symbol, current_price, direction, atr, precision
            )
            move_sign = "+" if direction == "BUY" else "-"

            if confidence >= 80.0 and net_advantage >= 30.0 and not any(v.veto for v in votes.values()):
                setup_grade = "A+ INSTITUTIONAL SETUP"
            elif confidence >= 75.0:
                setup_grade = "GRADE A HIGH CONVICTION"
            else:
                setup_grade = "GRADE B STANDARD SETUP"

            sweep_label = f" | Liquidity Sweep: {smc.liquidity_sweeps[0].sweep_type.replace('_', ' ')}" if smc and smc.liquidity_sweeps else ""

            reasoning = (
                f"[{setup_grade}] High-Conviction {direction} Signal ({confidence}% Confluence Score | Buy Score: {buy_score}, Sell Score: {sell_score}{sweep_label}). "
                f"Session Timing: {session_info.get('session_label')} ({session_info.get('quality')}). "
                f"Smart Money Flow: {smc.smc_bias} in {smc.premium_discount_zone.replace('_', ' ')} (Eq: ${smc.equilibrium_price:.2f}). "
                f"Execution Strategy: Phase 1 Entry @ ${entry:.2f} | Phase 2 TP1 ({move_sign}{tp1_dist:.2f} pts - Auto-Breakeven at trigger) | Phase 3 TP2 ({move_sign}{tp2_dist:.2f} pts - Trailing Stop) | Phase 4 TP3 ({move_sign}{tp3_dist:.2f} pts Runner Target). "
                f"Market Structure: {tech.market_structure.pattern if tech.market_structure else 'Trend'} with {mtf.alignment_score}% MTF synergy. "
                f"News Confirmation: {news_confirm.get('status')} ({news_sentiment.get('bullish')}% Bullish Sentiment). "
                f"SR Clearance: {tech.sr_buffer.verdict if tech.sr_buffer else 'Clear headroom'}."
            )
        else:
            entry = None
            stop_loss = None
            tp1 = None
            tp2 = None
            tp3 = None
            risk_reward = 0.0
            reasoning = (
                f"STAND ASIDE & WAIT (Confluence Score: {confidence}% | Buy: {buy_score}, Sell: {sell_score}, Net Advantage: {net_advantage} pts). "
                f"Session State: {session_info.get('session_label')} ({session_info.get('quality')}). "
                f"SMC State: {smc.institutional_verdict} "
                f"{event_risk.get('warning') if event_risk.get('news_risk') == 'HIGH' else tech.sr_buffer.verdict if (tech.sr_buffer and not tech.sr_buffer.has_sufficient_headroom) else 'Directional advantage is below institutional threshold (minimum 70% score + 25 pts edge required).'}"
            )


        now = datetime.datetime.now(datetime.timezone.utc)
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
            confidence=confidence,
            risk_reward=risk_reward,
            bias=bias,
            technical_summary=tech.summary,
            sentiment_summary=f"Sentiment: {news_sentiment.get('bias')} ({news_sentiment.get('bullish')}% Bullish / {news_sentiment.get('bearish')}% Bearish). {news_confirm.get('reasoning')}",
            risk_assessment=risk_vote.reasoning,
            reasoning=reasoning,
            analyst_votes_json={k: (v.model_dump() if hasattr(v, "model_dump") else v.dict()) for k, v in votes.items()},
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
        Background lifecycle evaluator with Phase 2 Auto-Breakeven & Trailing Stop:
        - When TP1 is hit (+1.5R) -> Move Stop-Loss to ENTRY (0.00 Risk-Free Shield)
        - When TP2 is hit (+2.5R) -> Trail Stop-Loss to TP1 (Lock in +1.5R guaranteed profit)
        - When TP3 is hit (+3.5R) -> Close trade as full runner victory
        - If price pulls back to Stop-Loss after TP1 -> Exit at BREAKEVEN (+0.5R scaled profit)
        - If price pulls back to Stop-Loss after TP2 -> Exit at TRAILED_WIN (+1.5R locked profit)
        """
        active_signals: List[Signal] = db.query(Signal).filter(Signal.status.in_(["ACTIVE", "TP1_HIT", "TP2_HIT"])).all()
        market_provider = get_market_data_provider()
        updates = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for sig in active_signals:
            current_price = market_provider.get_latest_price(str(sig.symbol))
            if not current_price or current_price <= 0:
                continue

            changed = False
            outcome = None

            entry_val = getattr(sig, "entry", None)
            sl_val = getattr(sig, "stop_loss", None)
            tp1_val = getattr(sig, "take_profit_1", None)
            tp2_val = getattr(sig, "take_profit_2", None)
            tp3_val = getattr(sig, "take_profit_3", None)

            entry_price: float = float(entry_val) if entry_val is not None else current_price
            sl_price: float = float(sl_val) if sl_val is not None else (entry_price * 0.99)
            tp1_price: float = float(tp1_val) if tp1_val is not None else (entry_price * 1.015)
            tp2_price: float = float(tp2_val) if tp2_val is not None else (entry_price * 1.025)
            tp3_price: float = float(tp3_val) if tp3_val is not None else (entry_price * 1.035)

            if sig.direction == "BUY":
                # 1. Full TP3 Win
                if current_price >= tp3_price:
                    sig.status = "TP3_HIT"  # type: ignore[assignment]
                    sig.closed_at = now  # type: ignore[assignment]
                    sig.exit_price = tp3_price  # type: ignore[assignment]
                    sig.pnl_r = 3.5  # type: ignore[assignment]
                    sig.pnl_percentage = round(((tp3_price - entry_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                    outcome = "WIN"
                    changed = True

                # 2. TP2 Hit -> Trail SL to TP1 (+1.5R locked)
                elif current_price >= tp2_price and sig.status != "TP2_HIT":
                    sig.status = "TP2_HIT"  # type: ignore[assignment]
                    sig.stop_loss = tp1_price  # type: ignore[assignment]  # Trailed stop loss to TP1!
                    changed = True

                # 3. TP1 Hit -> Move SL to Breakeven (Entry)
                elif current_price >= tp1_price and sig.status == "ACTIVE":
                    sig.status = "TP1_HIT"  # type: ignore[assignment]
                    sig.stop_loss = entry_price  # type: ignore[assignment]  # Auto-Breakeven activated!
                    changed = True

                # 4. Check Stop-Loss / Breakeven / Trailing Stop Trigger
                elif current_price <= sl_price:
                    if sig.status == "TP2_HIT":
                        # Stopped out on trailed stop at TP1
                        sig.status = "CLOSED"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = 1.5  # type: ignore[assignment]
                        sig.pnl_percentage = round(((sl_price - entry_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                        outcome = "WIN"
                        changed = True
                    elif sig.status == "TP1_HIT":
                        # Stopped out on breakeven
                        sig.status = "BREAKEVEN"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = 0.5  # type: ignore[assignment]  # Partial TP1 scale
                        sig.pnl_percentage = 0.0  # type: ignore[assignment]
                        outcome = "BREAKEVEN"
                        changed = True
                    else:
                        # Initial Stop-Loss hit
                        sig.status = "SL_HIT"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = -1.0  # type: ignore[assignment]
                        sig.pnl_percentage = round(((sl_price - entry_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                        outcome = "LOSS"
                        changed = True

            elif sig.direction == "SELL":
                # 1. Full TP3 Win
                if current_price <= tp3_price:
                    sig.status = "TP3_HIT"  # type: ignore[assignment]
                    sig.closed_at = now  # type: ignore[assignment]
                    sig.exit_price = tp3_price  # type: ignore[assignment]
                    sig.pnl_r = 3.5  # type: ignore[assignment]
                    sig.pnl_percentage = round(((entry_price - tp3_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                    outcome = "WIN"
                    changed = True

                # 2. TP2 Hit -> Trail SL to TP1 (+1.5R locked)
                elif current_price <= tp2_price and sig.status != "TP2_HIT":
                    sig.status = "TP2_HIT"  # type: ignore[assignment]
                    sig.stop_loss = tp1_price  # type: ignore[assignment]  # Trailed stop loss to TP1!
                    changed = True

                # 3. TP1 Hit -> Move SL to Breakeven (Entry)
                elif current_price <= tp1_price and sig.status == "ACTIVE":
                    sig.status = "TP1_HIT"  # type: ignore[assignment]
                    sig.stop_loss = entry_price  # type: ignore[assignment]  # Auto-Breakeven activated!
                    changed = True

                # 4. Check Stop-Loss / Breakeven / Trailing Stop Trigger
                elif current_price >= sl_price:
                    if sig.status == "TP2_HIT":
                        sig.status = "CLOSED"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = 1.5  # type: ignore[assignment]
                        sig.pnl_percentage = round(((entry_price - sl_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                        outcome = "WIN"
                        changed = True
                    elif sig.status == "TP1_HIT":
                        sig.status = "BREAKEVEN"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = 0.5  # type: ignore[assignment]
                        sig.pnl_percentage = 0.0  # type: ignore[assignment]
                        outcome = "BREAKEVEN"
                        changed = True
                    else:
                        sig.status = "SL_HIT"  # type: ignore[assignment]
                        sig.closed_at = now  # type: ignore[assignment]
                        sig.exit_price = sl_price  # type: ignore[assignment]
                        sig.pnl_r = -1.0  # type: ignore[assignment]
                        sig.pnl_percentage = round(((entry_price - sl_price) / entry_price) * 100.0, 2)  # type: ignore[assignment]
                        outcome = "LOSS"
                        changed = True

            if changed:
                if outcome:
                    signal_outcome = SignalOutcome(
                        signal_id=sig.id,
                        symbol=sig.symbol,
                        outcome=outcome,
                        pnl_r=sig.pnl_r or 0.0,
                        pnl_pct=sig.pnl_percentage or 0.0,
                        recorded_at=now
                    )
                    db.add(signal_outcome)
                
                db.commit()
                updates.append({"signal_id": sig.id, "symbol": sig.symbol, "new_status": sig.status, "stop_loss": sig.stop_loss})

        return updates

    @classmethod
    def auto_scan_and_generate_signals(cls, db: Session, target_count: int = 3) -> List[Signal]:
        """
        Background automated high-probability scanner:
        Scans global benchmark assets and persists top verified setups.
        """
        assets = ["XAUUSD", "BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "GBPUSD", "USDJPY", "USOIL", "NVDA", "NAS100", "AAPL", "TSLA"]
        generated = []
        for sym in assets:
            if len(generated) >= target_count:
                break
            try:
                sig = cls.generate_signal(db, symbol=sym, timeframe="1h")
                if sig.direction in ["BUY", "SELL"]:
                    generated.append(sig)
            except Exception as e:
                logger.error(f"Error auto-generating signal for {sym}: {e}")

        # If not enough BUY/SELL signals due to strict market conditions, also include the best evaluated signals
        if len(generated) < target_count:
            recent_sigs = db.query(Signal).order_by(Signal.created_at.desc()).limit(target_count).all()
            return recent_sigs

        return generated
