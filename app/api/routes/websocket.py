import asyncio
import json
import time
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.market import get_market_data_provider
from app.core.logging import logger

router = APIRouter(prefix="/ws", tags=["Real-Time WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.symbol_subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for sym, subs in self.symbol_subscriptions.items():
            if websocket in subs:
                subs.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining clients: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, symbol: str):
        symbol = symbol.upper()
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()
        self.symbol_subscriptions[symbol].add(websocket)

    def unsubscribe(self, websocket: WebSocket, symbol: str):
        symbol = symbol.upper()
        if symbol in self.symbol_subscriptions and websocket in self.symbol_subscriptions[symbol]:
            self.symbol_subscriptions[symbol].remove(websocket)

    async def broadcast_ticker_update(self, payload: dict):
        dead_sockets = []
        for socket in self.active_connections:
            try:
                await socket.send_json(payload)
            except Exception:
                dead_sockets.append(socket)
        for dead in dead_sockets:
            self.disconnect(dead)

    async def broadcast_symbol_update(self, symbol: str, payload: dict):
        symbol = symbol.upper()
        if symbol in self.symbol_subscriptions:
            dead_sockets = []
            for socket in self.symbol_subscriptions[symbol]:
                try:
                    await socket.send_json(payload)
                except Exception:
                    dead_sockets.append(socket)
            for dead in dead_sockets:
                self.disconnect(dead)

manager = ConnectionManager()
_broadcast_task = None

async def market_broadcast_loop():
    """Background loop that streams live real-time price updates to connected websockets"""
    while True:
        try:
            if manager.active_connections:
                market_provider = get_market_data_provider()
                tickers = market_provider.get_all_tickers()
                payload = {
                    "type": "TICKER_UPDATE",
                    "timestamp": time.time(),
                    "data": [t.dict() if hasattr(t, "dict") else t for t in tickers]
                }
                await manager.broadcast_ticker_update(payload)
                
                # Also send symbol-specific updates to subscribers
                for sym in list(manager.symbol_subscriptions.keys()):
                    ticker = market_provider.get_ticker(sym)
                    await manager.broadcast_symbol_update(sym, {
                        "type": "SYMBOL_TICK",
                        "symbol": sym,
                        "data": ticker.dict() if hasattr(ticker, "dict") else ticker
                    })
        except Exception as e:
            logger.debug(f"Broadcast loop tick error: {e}")
        
        await asyncio.sleep(1.5)

def ensure_broadcast_loop():
    global _broadcast_task
    if _broadcast_task is None or _broadcast_task.done():
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                _broadcast_task = loop.create_task(market_broadcast_loop())
        except Exception:
            pass

@router.websocket("/market")
async def websocket_market_endpoint(websocket: WebSocket):
    """
    Real-Time WebSocket Feed for Live Market Prices, Tickers, and Candle Updates.
    Clients can send JSON commands:
    - {"action": "subscribe", "symbol": "XAUUSD"}
    - {"action": "unsubscribe", "symbol": "XAUUSD"}
    - {"action": "ping"}
    """
    await manager.connect(websocket)
    ensure_broadcast_loop()
    market_provider = get_market_data_provider()
    
    # Send initial welcome & market snapshot
    try:
        tickers = market_provider.get_all_tickers()
        await websocket.send_json({
            "type": "INITIAL_SNAPSHOT",
            "timestamp": time.time(),
            "data": [t.dict() if hasattr(t, "dict") else t for t in tickers]
        })
    except Exception as e:
        logger.error(f"Error sending initial market snapshot: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "subscribe":
                    sym = msg.get("symbol", "XAUUSD")
                    manager.subscribe(websocket, sym)
                    await websocket.send_json({"type": "SUBSCRIBED", "symbol": sym})
                elif action == "unsubscribe":
                    sym = msg.get("symbol", "XAUUSD")
                    manager.unsubscribe(websocket, sym)
                    await websocket.send_json({"type": "UNSUBSCRIBED", "symbol": sym})
                elif action == "ping":
                    await websocket.send_json({"type": "PONG", "timestamp": time.time()})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket loop exception: {e}")
        manager.disconnect(websocket)
