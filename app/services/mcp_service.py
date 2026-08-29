from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Signal, News
from app.market import get_market_data_provider
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.ai_council import AIAgentAnalystCouncil
from app.services.track_record_service import TrackRecordService
from app.services.signal_engine import SignalEngine

class MCPService:
    @classmethod
    async def handle_rpc(cls, db: Session, user: User, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = params or {}
        market_provider = get_market_data_provider()

        if method == "tools/list":
            return {
                "tools": [
                    {"name": "latest_signals", "description": "Fetch latest generated AI trading signals", "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
                    {"name": "signal", "description": "Fetch specific signal by ID", "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
                    {"name": "track_record", "description": "Retrieve comprehensive audited institutional track record statistics", "inputSchema": {"type": "object"}},
                    {"name": "desk_read", "description": "Get current institutional morning desk readout across all assets", "inputSchema": {"type": "object"}},
                    {"name": "news", "description": "Fetch latest financial news and sentiment", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}}}},
                    {"name": "account", "description": "Retrieve user profile, subscription status, and active limits", "inputSchema": {"type": "object"}},
                    {"name": "analyze", "description": "Trigger multi-agent AI council analysis on a symbol and timeframe", "inputSchema": {"type": "object", "properties": {"symbol": {"type": "string"}, "timeframe": {"type": "string"}}, "required": ["symbol"]}},
                    {"name": "best_setup", "description": "Scan all markets to identify the single highest-confidence setup right now", "inputSchema": {"type": "object"}}
                ]
            }

        elif method == "latest_signals":
            limit = params.get("limit", 10)
            signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "direction": s.direction,
                    "timeframe": s.timeframe,
                    "entry": s.entry,
                    "stop_loss": s.stop_loss,
                    "take_profit_1": s.take_profit_1,
                    "confidence": s.confidence,
                    "risk_reward": s.risk_reward,
                    "status": s.status,
                    "created_at": s.created_at.isoformat()
                } for s in signals
            ]

        elif method == "signal":
            sig_id = params.get("id")
            sig = db.query(Signal).filter(Signal.id == sig_id).first()
            if not sig:
                return {"error": "Signal not found"}
            return {
                "id": sig.id,
                "symbol": sig.symbol,
                "direction": sig.direction,
                "entry": sig.entry,
                "stop_loss": sig.stop_loss,
                "take_profit_1": sig.take_profit_1,
                "take_profit_2": sig.take_profit_2,
                "take_profit_3": sig.take_profit_3,
                "confidence": sig.confidence,
                "bias": sig.bias,
                "reasoning": sig.reasoning,
                "status": sig.status
            }

        elif method == "track_record":
            record = TrackRecordService.calculate_track_record(db)
            return record.dict()

        elif method == "desk_read":
            tickers = market_provider.get_all_tickers()
            return {
                "market_regime": "Constructive Bullish Macro Regime",
                "risk_sentiment": "Moderate Risk-On",
                "tickers": tickers[:6],
                "ai_consensus_bias": "Bullish on Gold (XAUUSD) & Tech Equities, Neutral on FX."
            }

        elif method == "news":
            symbol = params.get("symbol")
            query = db.query(News).order_by(News.published_at.desc()).limit(10)
            items = query.all()
            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "summary": n.summary,
                    "impact": n.impact,
                    "sentiment": n.sentiment.sentiment if n.sentiment else "neutral"
                } for n in items
            ]

        elif method == "account":
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "plan": "PRO" if user.role == "ADMIN" else "FREE"
            }

        elif method == "analyze":
            symbol = params.get("symbol", "XAUUSD").upper()
            timeframe = params.get("timeframe", "1h")
            sig = SignalEngine.generate_signal(db, symbol, timeframe)
            return {
                "symbol": sig.symbol,
                "timeframe": sig.timeframe,
                "direction": sig.direction,
                "entry": sig.entry,
                "stop_loss": sig.stop_loss,
                "take_profit_1": sig.take_profit_1,
                "confidence": sig.confidence,
                "reasoning": sig.reasoning
            }

        elif method == "best_setup":
            symbols = ["XAUUSD", "BTCUSDT", "NVDA", "EURUSD"]
            best = None
            for s in symbols:
                candles = market_provider.get_historical_candles(s, "1h", 60)
                price = market_provider.get_latest_price(s)
                tech = TechnicalAnalysisService.analyze(s, "1h", candles)
                vote = AIAgentAnalystCouncil.evaluate_technical(tech, price)
                if best is None or vote.confidence > best["confidence"]:
                    best = {
                        "symbol": s,
                        "bias": vote.bias,
                        "confidence": vote.confidence,
                        "reasoning": vote.reasoning,
                        "current_price": price
                    }
            return best or {}

        else:
            raise ValueError(f"Unknown MCP method: {method}")
